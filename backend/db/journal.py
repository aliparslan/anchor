from datetime import datetime, timezone

from db.base import get_db


async def get_journal_dates() -> list[str]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT date FROM journal_entries WHERE content != '' ORDER BY date DESC"
        )
        rows = await cursor.fetchall()
        return [row["date"] for row in rows]
    finally:
        await db.close()


async def get_journal_entries_preview(limit: int = 20, offset: int = 0) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT date, SUBSTR(content, 1, 80) as preview FROM journal_entries WHERE content != '' ORDER BY date DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = await cursor.fetchall()
        return [{"date": row["date"], "preview": row["preview"]} for row in rows]
    finally:
        await db.close()


async def get_journal_entry(entry_date: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM journal_entries WHERE date = ?", (entry_date,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def append_journal_entry(entry_date: str, text: str) -> dict:
    """Append a timestamped line to an existing journal entry, or create one."""
    now = datetime.now()
    time_label = now.strftime("%-I:%M %p").lower()
    line = f"[{time_label}] {text}"
    existing = await get_journal_entry(entry_date)
    if existing and existing["content"]:
        content = existing["content"].rstrip() + "\n" + line
    else:
        content = line
    return await save_journal_entry(entry_date, content)


async def save_journal_entry(entry_date: str, content: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            """INSERT OR REPLACE INTO journal_entries (date, content, updated_at)
               VALUES (?, ?, ?)""",
            (entry_date, content, now),
        )
        await db.commit()
        return {"date": entry_date, "content": content, "updated_at": now}
    finally:
        await db.close()
