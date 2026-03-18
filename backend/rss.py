import asyncio

import aiohttp
import feedparser
from db import get_rss_feeds, save_rss_items, update_feed_fetched


async def _fetch_single_feed(session: aiohttp.ClientSession, feed: dict):
    """Fetch a single RSS/Atom feed and save new items."""
    try:
        async with session.get(
            feed["feed_url"],
            timeout=aiohttp.ClientTimeout(total=15),
            headers={"User-Agent": "Base Dashboard RSS Reader"},
        ) as resp:
            if resp.status != 200:
                print(f"[RSS] {feed['name']} returned HTTP {resp.status}")
                return
            text = await resp.text()
        loop = asyncio.get_event_loop()
        parsed = await loop.run_in_executor(None, feedparser.parse, text)
        items = []
        for entry in parsed.entries[:10]:
            items.append({
                "title": entry.get("title", "").strip(),
                "url": entry.get("link", ""),
                "author": entry.get("author", feed["name"]),
                "published_at": entry.get("published", ""),
                "guid": entry.get("id", entry.get("link", "")),
            })
        if items:
            await save_rss_items(feed["id"], items)
            await update_feed_fetched(feed["id"])
        print(f"[RSS] {feed['name']}: {len(items)} items")
    except Exception as e:
        print(f"[RSS] {feed['name']} failed: {e}")


async def fetch_all_feeds():
    """Fetch all RSS/Atom feeds concurrently and save new items."""
    feeds = await get_rss_feeds()
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[_fetch_single_feed(session, feed) for feed in feeds])
