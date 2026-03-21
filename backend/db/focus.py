from datetime import datetime, timezone

from db.base import get_db


async def get_pomodoro_sessions(session_date: str) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM pomodoro_sessions WHERE date = ? ORDER BY completed_at",
            (session_date,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def save_pomodoro_session(session_date: str, duration_minutes: int = 25) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            """INSERT INTO pomodoro_sessions (date, completed_at, duration_minutes)
               VALUES (?, ?, ?)""",
            (session_date, now, duration_minutes),
        )
        await db.commit()
        return {"date": session_date, "completed_at": now, "duration_minutes": duration_minutes}
    finally:
        await db.close()


async def get_pomodoro_total(session_date: str) -> int:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?",
            (session_date,),
        )
        row = await cursor.fetchone()
        return int(row["total"])
    finally:
        await db.close()
