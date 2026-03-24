import json

from db.base import get_db


async def save_github_contributions(data: dict):
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("github_contributions", json.dumps(data)),
        )
        await db.commit()
    finally:
        await db.close()


async def get_github_contributions() -> dict:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT value FROM settings WHERE key = ?",
            ("github_contributions",),
        )
        row = await cursor.fetchone()
        if row:
            return json.loads(row["value"])
        return {}
    finally:
        await db.close()
