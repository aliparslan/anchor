from datetime import datetime, timezone

from db.base import get_db


async def get_mit(entry_date: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM daily_mit WHERE date = ?", (entry_date,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def save_mit(entry_date: str, text: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            """INSERT OR REPLACE INTO daily_mit (date, text, completed, updated_at)
               VALUES (?, ?, COALESCE((SELECT completed FROM daily_mit WHERE date = ?), 0), ?)""",
            (entry_date, text, entry_date, now),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT * FROM daily_mit WHERE date = ?", (entry_date,)
        )
        row = await cursor.fetchone()
        return dict(row)
    finally:
        await db.close()


async def toggle_mit(entry_date: str) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT completed FROM daily_mit WHERE date = ?", (entry_date,)
        )
        row = await cursor.fetchone()
        new_val = 0 if (row and row["completed"]) else 1
        now = datetime.now(timezone.utc).isoformat()
        if row:
            await db.execute(
                "UPDATE daily_mit SET completed = ?, updated_at = ? WHERE date = ?",
                (new_val, now, entry_date),
            )
        else:
            await db.execute(
                "INSERT INTO daily_mit (date, text, completed, updated_at) VALUES (?, '', ?, ?)",
                (entry_date, new_val, now),
            )
        await db.commit()
        return bool(new_val)
    finally:
        await db.close()
