from db.base import get_db


async def search_all(query: str, limit: int = 20) -> dict:
    db = await get_db()
    q = f"%{query}%"
    try:
        results = {"journal": [], "queue": [], "rss": []}
        # Journal
        cur = await db.execute(
            "SELECT date, content FROM journal_entries WHERE content LIKE ? ORDER BY date DESC LIMIT ?",
            (q, limit),
        )
        results["journal"] = [dict(r) for r in await cur.fetchall()]
        # Reading queue
        cur = await db.execute(
            "SELECT id, title, url, domain FROM reading_queue WHERE title LIKE ? ORDER BY saved_at DESC LIMIT ?",
            (q, limit),
        )
        results["queue"] = [dict(r) for r in await cur.fetchall()]
        # RSS items
        cur = await db.execute(
            "SELECT ri.id, ri.title, ri.url, rf.name as feed_name FROM rss_items ri JOIN rss_feeds rf ON ri.feed_id = rf.id WHERE ri.title LIKE ? ORDER BY ri.published_at DESC LIMIT ?",
            (q, limit),
        )
        results["rss"] = [dict(r) for r in await cur.fetchall()]
        return results
    finally:
        await db.close()
