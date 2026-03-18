import asyncio
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from curl_cffi.requests import AsyncSession

from db import save_youtube_videos

DATA_DIR = Path(__file__).parent.parent / "data"
COOKIES_FILE = DATA_DIR / "yt_cookies.txt"


def parse_netscape_cookies(path: Path, domains: list[str] | None = None) -> dict[str, str]:
    """Parse Netscape cookie file, optionally filtering to specific domains."""
    cookies = {}
    if not path.exists():
        return cookies
    if domains is None:
        domains = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                if line.startswith("#HttpOnly_"):
                    line = line[len("#HttpOnly_"):]
                else:
                    continue
            parts = line.split("\t")
            if len(parts) >= 7:
                domain = parts[0].lstrip(".")
                if domains and not any(domain.endswith(d) for d in domains):
                    continue
                name = parts[5]
                value = parts[6]
                cookies[name] = value
    return cookies


def parse_duration(text: str) -> tuple[int, str]:
    """Parse duration like '12:34' or '1:23:45' into seconds and label."""
    if not text:
        return 0, ""
    parts = text.strip().split(":")
    try:
        if len(parts) == 3:
            seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            seconds = int(parts[0]) * 60 + int(parts[1])
        else:
            seconds = int(parts[0])
        return seconds, text.strip()
    except ValueError:
        return 0, text.strip()


def format_duration(seconds: int) -> str:
    """Format seconds into H:MM:SS or M:SS."""
    if seconds <= 0:
        return ""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def extract_videos_from_initial_data(data: dict) -> list[dict]:
    """Extract videos from ytInitialData, supporting both old and new YouTube formats."""
    videos = []
    seen_ids = set()

    try:
        tabs = data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]
        grid = tabs[0]["tabRenderer"]["content"]["richGridRenderer"]
        items = grid.get("contents", [])
    except (KeyError, IndexError):
        return videos

    def process_items(item_list: list):
        for item in item_list:
            if "richItemRenderer" in item:
                content = item["richItemRenderer"].get("content", {})

                # New format: lockupViewModel
                if "lockupViewModel" in content:
                    process_lockup(content["lockupViewModel"])

                # Old format: videoRenderer
                elif "videoRenderer" in content:
                    process_video_renderer(content["videoRenderer"])

            elif "richSectionRenderer" in item:
                section_content = item["richSectionRenderer"].get("content", {})
                shelf = section_content.get("richShelfRenderer", {})
                if shelf:
                    process_items(shelf.get("contents", []))

    def process_lockup(lockup: dict):
        content_type = lockup.get("contentType", "")
        if content_type != "LOCKUP_CONTENT_TYPE_VIDEO":
            return

        video_id = lockup.get("contentId", "")
        if not video_id or video_id in seen_ids:
            return

        meta = lockup.get("metadata", {}).get("lockupMetadataViewModel", {})
        title = meta.get("title", {}).get("content", "")

        channel = ""
        content_meta = meta.get("metadata", {}).get("contentMetadataViewModel", {})
        for row in content_meta.get("metadataRows", []):
            for part in row.get("metadataParts", []):
                text = part.get("text", {}).get("content", "")
                if text and not channel:
                    channel = text
                    break
            if channel:
                break

        thumb_vm = lockup.get("contentImage", {}).get("thumbnailViewModel", {})
        sources = thumb_vm.get("image", {}).get("sources", [])
        thumbnail = sources[-1]["url"] if sources else ""

        duration_text = ""
        for overlay in thumb_vm.get("overlays", []):
            bottom = overlay.get("thumbnailBottomOverlayViewModel", {})
            for badge in bottom.get("badges", []):
                badge_vm = badge.get("thumbnailBadgeViewModel", {})
                text = badge_vm.get("text", "")
                if text and ":" in text:
                    duration_text = text
                    break

        duration_seconds, duration_label = parse_duration(duration_text)

        if 0 < duration_seconds < 60:
            return
        if "#shorts" in title.lower():
            return

        seen_ids.add(video_id)
        videos.append(
            {
                "video_id": video_id,
                "title": title,
                "channel": channel,
                "thumbnail": thumbnail,
                "duration_seconds": duration_seconds,
                "duration_label": duration_label,
            }
        )

    def process_video_renderer(renderer: dict):
        video_id = renderer.get("videoId", "")
        if not video_id or video_id in seen_ids:
            return

        title_runs = renderer.get("title", {}).get("runs", [])
        title = title_runs[0]["text"] if title_runs else ""

        channel_runs = renderer.get("ownerText", {}).get("runs", [])
        if not channel_runs:
            channel_runs = renderer.get("longBylineText", {}).get("runs", [])
        channel = channel_runs[0]["text"] if channel_runs else ""

        thumbnails = renderer.get("thumbnail", {}).get("thumbnails", [])
        thumbnail = thumbnails[-1]["url"] if thumbnails else ""

        duration_text = renderer.get("lengthText", {}).get("simpleText", "")
        duration_seconds, duration_label = parse_duration(duration_text)

        if 0 < duration_seconds < 60:
            return

        for overlay in renderer.get("thumbnailOverlays", []):
            style = overlay.get("thumbnailOverlayTimeStatusRenderer", {}).get("style", "")
            if style == "SHORTS":
                return

        seen_ids.add(video_id)
        videos.append(
            {
                "video_id": video_id,
                "title": title,
                "channel": channel,
                "thumbnail": thumbnail,
                "duration_seconds": duration_seconds,
                "duration_label": duration_label,
            }
        )

    process_items(items)
    return videos


async def _fetch_via_scrape(cookies: dict[str, str]) -> tuple[list[dict], bool]:
    """Scrape YouTube homepage. Returns (videos, is_authenticated)."""
    cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())

    headers = {
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": cookie_header,
    }
    sapisid = cookies.get("SAPISID") or cookies.get("__Secure-3PAPISID", "")
    if sapisid:
        origin = "https://www.youtube.com"
        timestamp = str(int(time.time()))
        hash_input = f"{timestamp} {sapisid} {origin}"
        sha1 = hashlib.sha1(hash_input.encode()).hexdigest()
        headers["Authorization"] = f"SAPISIDHASH {timestamp}_{sha1}"
        headers["Origin"] = origin
        headers["X-Origin"] = origin

    async with AsyncSession(impersonate="chrome") as session:
        resp = await session.get(
            "https://www.youtube.com",
            headers=headers,
            allow_redirects=True,
            timeout=30,
        )
        resp.raise_for_status()
        html = resp.text

    is_authenticated = '"LOGGED_IN":true' in html

    # Extract ytInitialData
    marker = re.search(r"var ytInitialData\s*=\s*\{", html)
    if not marker:
        marker = re.search(r'window\["ytInitialData"\]\s*=\s*\{', html)
    if not marker:
        return [], is_authenticated

    start = marker.end() - 1
    depth = 0
    i = start
    while i < len(html):
        ch = html[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        elif ch == '"':
            i += 1
            while i < len(html) and html[i] != '"':
                if html[i] == "\\":
                    i += 1
                i += 1
        i += 1

    try:
        data = json.loads(html[start : i + 1])
    except json.JSONDecodeError:
        return [], is_authenticated

    return extract_videos_from_initial_data(data), is_authenticated


async def _fetch_via_ytdlp() -> list[dict]:
    """Fallback: use yt-dlp to get YouTube homepage videos."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "uv", "run", "yt-dlp",
            "--cookies", str(COOKIES_FILE),
            "--flat-playlist", "--dump-json", "--no-warnings",
            "--playlist-items", "1:15",
            "https://www.youtube.com",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=90)
    except (asyncio.TimeoutError, FileNotFoundError):
        return []

    videos = []
    seen = set()
    for line in stdout.decode().strip().split("\n"):
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        vid = entry.get("id", "")
        if not vid or vid in seen:
            continue

        duration = entry.get("duration") or 0
        if 0 < duration < 60:
            continue

        title = entry.get("title", "")
        if "#shorts" in title.lower():
            continue

        seen.add(vid)
        videos.append(
            {
                "video_id": vid,
                "title": title,
                "channel": entry.get("channel", "") or entry.get("uploader", ""),
                "thumbnail": f"https://i.ytimg.com/vi/{vid}/hq720.jpg",
                "duration_seconds": duration,
                "duration_label": format_duration(duration),
            }
        )

    return videos


async def fetch_youtube_recommendations(count: int = 10) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    cookies = parse_netscape_cookies(COOKIES_FILE, domains=["youtube.com", "google.com"])

    if not cookies:
        print("[YouTube] No cookies found. Export cookies to data/yt_cookies.txt")
        return []

    # Try scraping first
    videos, is_authenticated = await _fetch_via_scrape(cookies)

    if not is_authenticated:
        print("[YouTube] Warning: cookies did not authenticate. Recommendations may not be personalized.")
        print("[YouTube] Re-export cookies from youtube.com using 'Current Site' option.")

    # If scraping got nothing or not authenticated, try yt-dlp as fallback
    if not videos:
        print("[YouTube] Scrape returned no videos, trying yt-dlp fallback...")
        videos = await _fetch_via_ytdlp()

    videos = videos[:count]

    for video in videos:
        video["fetched_at"] = now

    await save_youtube_videos(videos)
    print(f"[YouTube] Saved {len(videos)} videos (authenticated: {is_authenticated})")
    return videos
