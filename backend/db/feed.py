from datetime import datetime, timezone

from db.base import get_db


# --- HN ---


async def get_latest_hn_posts(limit: int = 10):
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT * FROM hn_posts
               ORDER BY fetched_at DESC, score DESC
               LIMIT ?""",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def save_hn_posts(posts: list[dict]):
    db = await get_db()
    try:
        # Clear old posts
        await db.execute("DELETE FROM hn_posts")
        for post in posts:
            await db.execute(
                """INSERT OR REPLACE INTO hn_posts
                   (hn_id, title, url, domain, score, comments, hn_url, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    post["hn_id"],
                    post["title"],
                    post.get("url", ""),
                    post.get("domain", ""),
                    post.get("score", 0),
                    post.get("comments", 0),
                    post["hn_url"],
                    post["fetched_at"],
                ),
            )
        await db.commit()
    finally:
        await db.close()


# --- YouTube ---


async def get_latest_youtube_videos(limit: int = 10):
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT * FROM youtube_videos
               ORDER BY fetched_at DESC
               LIMIT ?""",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def save_youtube_videos(videos: list[dict]):
    db = await get_db()
    try:
        # Clear old videos
        await db.execute("DELETE FROM youtube_videos")
        for video in videos:
            await db.execute(
                """INSERT OR REPLACE INTO youtube_videos
                   (video_id, title, channel, thumbnail, duration_seconds, duration_label, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    video["video_id"],
                    video["title"],
                    video.get("channel", ""),
                    video.get("thumbnail", ""),
                    video.get("duration_seconds", 0),
                    video.get("duration_label", ""),
                    video["fetched_at"],
                ),
            )
        await db.commit()
    finally:
        await db.close()


async def dismiss_video(video_id: str):
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO dismissed_videos (video_id, dismissed_at) VALUES (?, ?)",
            (video_id, now),
        )
        await db.commit()
    finally:
        await db.close()


async def get_dismissed_video_ids() -> list[str]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT video_id FROM dismissed_videos")
        rows = await cursor.fetchall()
        return [row["video_id"] for row in rows]
    finally:
        await db.close()


# --- Reading Queue ---


async def get_reading_queue() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM reading_queue WHERE read_at IS NULL ORDER BY saved_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def save_to_reading_queue(hn_id: int | None, title: str, url: str, domain: str | None) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO reading_queue (hn_id, title, url, domain, saved_at)
               VALUES (?, ?, ?, ?, ?)""",
            (hn_id, title, url, domain, now),
        )
        await db.commit()
        item_id = cursor.lastrowid
        cur = await db.execute("SELECT * FROM reading_queue WHERE id = ?", (item_id,))
        row = await cur.fetchone()
        return dict(row)
    finally:
        await db.close()


async def mark_queue_item_read(item_id: int):
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            "UPDATE reading_queue SET read_at = ? WHERE id = ?", (now, item_id)
        )
        await db.commit()
    finally:
        await db.close()


async def delete_queue_item(item_id: int):
    db = await get_db()
    try:
        await db.execute("DELETE FROM reading_queue WHERE id = ?", (item_id,))
        await db.commit()
    finally:
        await db.close()


async def delete_queue_item_by_hn_id(hn_id: int):
    db = await get_db()
    try:
        await db.execute("DELETE FROM reading_queue WHERE hn_id = ?", (hn_id,))
        await db.commit()
    finally:
        await db.close()


async def mark_queue_item_unread(item_id: int):
    db = await get_db()
    try:
        await db.execute("UPDATE reading_queue SET read_at = NULL WHERE id = ?", (item_id,))
        await db.commit()
    finally:
        await db.close()


# --- RSS ---


SEED_FEEDS = [
    ("Stratechery", "https://stratechery.com/feed/", "https://stratechery.com"),
    ("Simon Willison", "https://simonwillison.net/atom/everything/", "https://simonwillison.net"),
    ("Daring Fireball", "https://daringfireball.net/feeds/main", "https://daringfireball.net"),
    ("Seth Godin", "https://feeds.feedblitz.com/sethsblog", "https://seths.blog"),
    ("The Hustle", "https://thehustle.co/feed/", "https://thehustle.co"),
    ("Paul Graham", "http://www.aaronsw.com/2002/feeds/pgessays.rss", "https://paulgraham.com"),
    ("Cal Newport", "https://calnewport.com/feed/", "https://calnewport.com"),
]


async def seed_rss_feeds():
    db = await get_db()
    try:
        for name, feed_url, site_url in SEED_FEEDS:
            await db.execute(
                "INSERT OR IGNORE INTO rss_feeds (name, feed_url, site_url) VALUES (?, ?, ?)",
                (name, feed_url, site_url),
            )
        await db.commit()
    finally:
        await db.close()


async def get_rss_feeds() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM rss_feeds ORDER BY name")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_rss_items(limit: int = 50) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT ri.*, rf.name as feed_name, rf.site_url
               FROM rss_items ri
               JOIN rss_feeds rf ON ri.feed_id = rf.id
               ORDER BY ri.published_at DESC, ri.fetched_at DESC
               LIMIT ?""",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def save_rss_items(feed_id: int, items: list[dict]):
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        for item in items:
            await db.execute(
                """INSERT OR IGNORE INTO rss_items
                   (feed_id, title, url, author, published_at, fetched_at, guid)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    feed_id,
                    item["title"],
                    item["url"],
                    item.get("author", ""),
                    item.get("published_at", ""),
                    now,
                    item.get("guid", item["url"]),
                ),
            )
        await db.commit()
    finally:
        await db.close()


async def add_rss_feed(name: str, feed_url: str, site_url: str) -> dict:
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO rss_feeds (name, feed_url, site_url) VALUES (?, ?, ?)",
            (name, feed_url, site_url),
        )
        await db.commit()
        cur = await db.execute("SELECT * FROM rss_feeds WHERE id = ?", (cursor.lastrowid,))
        row = await cur.fetchone()
        return dict(row)
    finally:
        await db.close()


async def delete_rss_feed(feed_id: int):
    db = await get_db()
    try:
        await db.execute("DELETE FROM rss_items WHERE feed_id = ?", (feed_id,))
        await db.execute("DELETE FROM rss_feeds WHERE id = ?", (feed_id,))
        await db.commit()
    finally:
        await db.close()


async def dismiss_rss_item(item_id: int):
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR IGNORE INTO dismissed_rss (item_id, dismissed_at) VALUES (?, ?)",
            (item_id, now),
        )
        await db.commit()
    finally:
        await db.close()


async def get_dismissed_rss_ids() -> list[int]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT item_id FROM dismissed_rss")
        rows = await cursor.fetchall()
        return [row["item_id"] for row in rows]
    finally:
        await db.close()


async def update_feed_fetched(feed_id: int):
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            "UPDATE rss_feeds SET last_fetched_at = ? WHERE id = ?",
            (now, feed_id),
        )
        await db.commit()
    finally:
        await db.close()
