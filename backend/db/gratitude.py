from datetime import datetime, timezone

from db.base import get_db


async def get_gratitudes() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM gratitude_jar ORDER BY created_at DESC")
        return [dict(row) for row in await cursor.fetchall()]
    finally:
        await db.close()


async def save_gratitude(text: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO gratitude_jar (text, created_at) VALUES (?, ?)", (text, now)
        )
        await db.commit()
        cur = await db.execute("SELECT * FROM gratitude_jar WHERE id = ?", (cursor.lastrowid,))
        return dict(await cur.fetchone())
    finally:
        await db.close()


async def get_random_gratitude() -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM gratitude_jar ORDER BY RANDOM() LIMIT 1")
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()
