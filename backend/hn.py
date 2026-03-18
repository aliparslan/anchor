import asyncio
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from db import save_hn_posts

HN_API = "https://hacker-news.firebaseio.com/v0"


async def fetch_item(client: httpx.AsyncClient, item_id: int) -> dict | None:
    try:
        resp = await client.get(f"{HN_API}/item/{item_id}.json")
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def extract_domain(url: str) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


async def fetch_top_hn_posts(count: int = 10) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{HN_API}/topstories.json")
        resp.raise_for_status()
        story_ids = resp.json()[:50]  # Fetch top 50, then pick best 10

        tasks = [fetch_item(client, sid) for sid in story_ids]
        items = await asyncio.gather(*tasks)

    posts = []
    for item in items:
        if not item or item.get("type") != "story":
            continue
        url = item.get("url", "")
        posts.append(
            {
                "hn_id": item["id"],
                "title": item.get("title", ""),
                "url": url,
                "domain": extract_domain(url),
                "score": item.get("score", 0),
                "comments": item.get("descendants", 0),
                "hn_url": f"https://news.ycombinator.com/item?id={item['id']}",
                "fetched_at": now,
            }
        )

    posts.sort(key=lambda p: p["score"], reverse=True)
    top_posts = posts[:count]

    await save_hn_posts(top_posts)
    print(f"[HN] Saved {len(top_posts)} posts")
    return top_posts
