import asyncio
import json
import logging
import platform
import time
from datetime import date
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
import psutil

from db import (
    get_setting,
    save_setting,
    save_push_subscription,
    delete_push_subscription,
    get_rss_feeds,
    add_rss_feed,
    delete_rss_feed,
    get_pomodoro_sessions,
    save_pomodoro_session,
    get_mit,
    save_mit,
    toggle_mit,
    get_gratitudes,
    save_gratitude,
    get_random_gratitude,
    search_all,
)
from weather import geocode_zip, fetch_weather

logger = logging.getLogger(__name__)

router = APIRouter()


class ZipBody(BaseModel):
    zip_code: str = Field(max_length=20)


class PushSubscriptionBody(BaseModel):
    endpoint: str = Field(max_length=2000)
    p256dh: str = Field(max_length=500)
    auth: str = Field(max_length=500)


class TimerScheduleBody(BaseModel):
    fire_at: float  # Unix timestamp in seconds
    title: str = Field(default="Anchor", max_length=200)
    body: str = Field(default="Timer complete!", max_length=2000)


class MitBody(BaseModel):
    text: str = Field(max_length=2000)


class PreferencesBody(BaseModel):
    name: str | None = None
    pomo_duration: int | None = None
    focus_goal: int | None = None


class FeedBody(BaseModel):
    name: str = Field(max_length=200)
    feed_url: str = Field(max_length=2000)
    site_url: str = Field(max_length=2000)


class GitHubBody(BaseModel):
    username: str = Field(max_length=200)
    token: str = Field(default="", max_length=500)


class GratitudeBody(BaseModel):
    text: str = Field(max_length=2000)


# --- Preferences ---


@router.get("/api/settings/preferences")
async def api_get_preferences():
    name = await get_setting("user_name") or "Alip"
    pomo_duration = int(await get_setting("pomo_duration") or 25)
    focus_goal = int(await get_setting("focus_goal") or 240)
    return {"name": name, "pomo_duration": pomo_duration, "focus_goal": focus_goal}


@router.put("/api/settings/preferences")
async def api_set_preferences(body: PreferencesBody):
    if body.name is not None:
        await save_setting("user_name", body.name)
    if body.pomo_duration is not None:
        await save_setting("pomo_duration", str(body.pomo_duration))
    if body.focus_goal is not None:
        await save_setting("focus_goal", str(body.focus_goal))
    return await api_get_preferences()


# --- GitHub ---


@router.get("/api/settings/github")
async def api_get_github():
    username = await get_setting("github_username") or ""
    token = await get_setting("github_token") or ""
    return {"username": username, "connected": bool(token)}


@router.put("/api/settings/github")
async def api_set_github(body: GitHubBody):
    await save_setting("github_username", body.username)
    if body.token:
        await save_setting("github_token", body.token)
    return {"username": body.username, "connected": bool(body.token)}


# --- YouTube Cookies ---

COOKIES_FILE = Path(__file__).parent.parent.parent / "data" / "yt_cookies.txt"


class YouTubeCookiesBody(BaseModel):
    cookies: str


@router.get("/api/settings/youtube-cookies")
async def api_get_youtube_cookies():
    if COOKIES_FILE.exists():
        text = COOKIES_FILE.read_text()
        lines = [l for l in text.strip().splitlines() if l.strip() and not l.startswith("# ")]
        return {"has_cookies": True, "line_count": len(lines)}
    return {"has_cookies": False, "line_count": 0}


@router.put("/api/settings/youtube-cookies")
async def api_set_youtube_cookies(body: YouTubeCookiesBody):
    COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    COOKIES_FILE.write_text(body.cookies)
    return await api_get_youtube_cookies()


# --- Feeds ---


@router.get("/api/settings/feeds")
async def api_get_feeds():
    feeds = await get_rss_feeds()
    return {"feeds": feeds}


@router.post("/api/settings/feeds")
async def api_add_feed(body: FeedBody):
    feed = await add_rss_feed(body.name, body.feed_url, body.site_url)
    return {"feed": feed}


@router.delete("/api/settings/feeds/{feed_id}")
async def api_delete_feed(feed_id: int):
    await delete_rss_feed(feed_id)
    return {"ok": True}


# --- Push ---


@router.get("/api/push/vapid-key")
async def api_vapid_key(request: Request):
    return {"public_key": request.app.state.vapid_public_key}


@router.post("/api/push/subscribe")
async def api_push_subscribe(body: PushSubscriptionBody):
    await save_push_subscription(body.endpoint, body.p256dh, body.auth)
    return {"ok": True}


@router.delete("/api/push/subscribe")
async def api_push_unsubscribe(body: PushSubscriptionBody):
    await delete_push_subscription(body.endpoint)
    return {"ok": True}


@router.post("/api/push/test")
async def api_push_test(request: Request):
    send_push_to_all = request.app.state.send_push_to_all
    await send_push_to_all("Base", "Test notification ✦")
    return {"ok": True}


# Timer push notification scheduling
_timer_task: asyncio.Task | None = None


@router.post("/api/push/schedule-timer")
async def api_schedule_timer(req: TimerScheduleBody, request: Request):
    global _timer_task
    if _timer_task and not _timer_task.done():
        _timer_task.cancel()

    send_push_to_all = request.app.state.send_push_to_all

    async def _fire():
        delay = max(0, req.fire_at - time.time())
        await asyncio.sleep(delay)
        await send_push_to_all(req.title, req.body)

    _timer_task = asyncio.create_task(_fire())
    return {"ok": True}


@router.delete("/api/push/schedule-timer")
async def api_cancel_timer():
    global _timer_task
    if _timer_task and not _timer_task.done():
        _timer_task.cancel()
        _timer_task = None
    return {"ok": True}


# --- Status ---


@router.get("/api/status/system")
async def api_system_status():
    hostname = platform.node()

    # Uptime
    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    mins = (uptime_seconds % 3600) // 60
    uptime_str = f"{days}d {hours}h {mins}m" if days > 0 else f"{hours}h {mins}m"

    # CPU
    cpu_percent = await asyncio.get_event_loop().run_in_executor(
        None, lambda: psutil.cpu_percent(interval=0.5)
    )

    # Memory
    mem = psutil.virtual_memory()

    # Disk
    # On macOS, "/" reports APFS container size; use home dir for user-accessible space
    if platform.system() == "Darwin":
        disk = psutil.disk_usage(str(Path.home()))
    else:
        disk = psutil.disk_usage("/")

    return {
        "hostname": hostname,
        "uptime": uptime_str,
        "cpu_percent": round(cpu_percent, 1),
        "memory": {
            "total_gb": round(mem.total / (1024**3), 1),
            "used_gb": round(mem.used / (1024**3), 1),
            "percent": mem.percent,
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 1),
            "used_gb": round(disk.used / (1024**3), 1),
            "percent": round(disk.percent, 1),
        },
    }


@router.get("/api/status/claude")
async def api_claude_status():
    stats_path = Path.home() / ".claude" / "stats-cache.json"
    if not stats_path.exists():
        return {"available": False}
    try:
        data = json.loads(stats_path.read_text())
        return {
            "available": True,
            "total_messages": data.get("totalMessages", 0),
            "total_sessions": data.get("totalSessions", 0),
            "daily_activity": data.get("dailyActivity", [])[-7:],
            "model_usage": data.get("modelUsage", {}),
            "last_computed": data.get("lastComputedDate", ""),
        }
    except Exception:
        logger.exception("Claude API status fetch failed")
        return {"available": False}


@router.get("/api/status/tailscale")
async def api_tailscale_status():
    try:
        proc = await asyncio.create_subprocess_exec(
            "tailscale", "status", "--json",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        except asyncio.TimeoutError:
            return {"available": False}
        if proc.returncode != 0:
            return {"available": False}
        data = json.loads(stdout.decode())
        peers = []
        for peer_id, peer in data.get("Peer", {}).items():
            peers.append({
                "hostname": peer.get("HostName", ""),
                "os": peer.get("OS", ""),
                "online": peer.get("Online", False),
                "ip": peer.get("TailscaleIPs", [""])[0] if peer.get("TailscaleIPs") else "",
            })
        self_node = data.get("Self", {})
        return {
            "available": True,
            "self": {
                "hostname": self_node.get("HostName", ""),
                "ip": self_node.get("TailscaleIPs", [""])[0] if self_node.get("TailscaleIPs") else "",
                "online": True,
            },
            "peers": peers,
        }
    except Exception:
        logger.exception("Tailscale status fetch failed")
        return {"available": False}


# --- Weather ---


@router.get("/api/weather")
async def api_weather():
    coords_raw = await get_setting("weather_coords")
    zip_code = await get_setting("weather_zip")
    if not coords_raw:
        return {"weather": None, "zip_code": zip_code}
    coords = json.loads(coords_raw)
    weather = await fetch_weather(coords["lat"], coords["lon"])
    return {"weather": weather, "zip_code": zip_code, "location": coords.get("name", "")}


@router.put("/api/weather/zip")
async def api_set_zip(body: ZipBody):
    coords = await geocode_zip(body.zip_code)
    if not coords:
        raise HTTPException(status_code=404, detail="Could not find location")
    await save_setting("weather_zip", body.zip_code)
    await save_setting("weather_coords", json.dumps(coords))
    weather = await fetch_weather(coords["lat"], coords["lon"])
    return {"weather": weather, "zip_code": body.zip_code, "location": coords.get("name", "")}


# --- Pomodoro ---


@router.get("/api/pomodoro/today")
async def api_pomodoro_today():
    today = date.today().isoformat()
    sessions = await get_pomodoro_sessions(today)
    total_minutes = sum(s["duration_minutes"] for s in sessions)
    return {"sessions": sessions, "total_minutes": total_minutes}


@router.post("/api/pomodoro/complete")
async def api_pomodoro_complete():
    today = date.today().isoformat()
    pomo_duration = int(await get_setting("pomo_duration") or 25)
    await save_pomodoro_session(today, pomo_duration)
    sessions = await get_pomodoro_sessions(today)
    total_minutes = sum(s["duration_minutes"] for s in sessions)
    return {"sessions": sessions, "total_minutes": total_minutes}


# --- MIT ---


@router.get("/api/mit/today")
async def api_mit_today():
    today = date.today().isoformat()
    mit = await get_mit(today)
    return {"mit": mit}


@router.put("/api/mit/today")
async def api_save_mit_today(body: MitBody):
    today = date.today().isoformat()
    mit = await save_mit(today, body.text)
    return {"mit": mit}


@router.post("/api/mit/today/toggle")
async def api_toggle_mit_today():
    today = date.today().isoformat()
    completed = await toggle_mit(today)
    return {"completed": completed}


# --- Gratitude ---


@router.get("/api/gratitude")
async def api_gratitudes():
    items = await get_gratitudes()
    return {"items": items}


@router.post("/api/gratitude")
async def api_save_gratitude(body: GratitudeBody):
    item = await save_gratitude(body.text)
    return {"item": item}


@router.get("/api/gratitude/random")
async def api_random_gratitude():
    item = await get_random_gratitude()
    return {"item": item}


# --- Search ---


@router.get("/api/search")
async def api_search(q: str = ""):
    if not q.strip():
        return {"results": {"journal": [], "queue": [], "rss": []}}
    results = await search_all(q.strip())
    return {"results": results}


# --- Dashboard Age ---


@router.get("/api/status/age")
async def api_dashboard_age():
    first_launch = await get_setting("first_launch_date")
    if not first_launch:
        today = date.today().isoformat()
        await save_setting("first_launch_date", today)
        first_launch = today
    days = (date.today() - date.fromisoformat(first_launch)).days
    return {"days": days, "since": first_launch}
