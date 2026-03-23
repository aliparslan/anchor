from datetime import datetime, date, timedelta, timezone

from db.base import get_db


# --- Sleep ---


async def get_sleep_week(today_str: str) -> list[dict]:
    today = date.fromisoformat(today_str)
    start = (today - timedelta(days=29)).isoformat()
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT date, bedtime, wake_time FROM sleep_log
               WHERE date >= ? AND date <= ?
               ORDER BY date ASC""",
            (start, today_str),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_sleep_log(entry_date: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM sleep_log WHERE date = ?", (entry_date,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def save_sleep_log(entry_date: str, bedtime: str, wake_time: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            """INSERT OR REPLACE INTO sleep_log (date, bedtime, wake_time, updated_at)
               VALUES (?, ?, ?, ?)""",
            (entry_date, bedtime, wake_time, now),
        )
        await db.commit()
        return {"date": entry_date, "bedtime": bedtime, "wake_time": wake_time, "updated_at": now}
    finally:
        await db.close()


# --- Workout ---


async def get_workout(entry_date: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM workout_log WHERE date = ?", (entry_date,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def toggle_workout(entry_date: str) -> bool:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT completed FROM workout_log WHERE date = ?", (entry_date,)
        )
        row = await cursor.fetchone()
        new_val = 0 if (row and row["completed"]) else 1
        now = datetime.now(timezone.utc).isoformat()
        if row:
            await db.execute(
                "UPDATE workout_log SET completed = ?, updated_at = ? WHERE date = ?",
                (new_val, now, entry_date),
            )
        else:
            await db.execute(
                "INSERT INTO workout_log (date, completed, note, updated_at) VALUES (?, ?, '', ?)",
                (entry_date, new_val, now),
            )
        await db.commit()
        return bool(new_val)
    finally:
        await db.close()


async def save_workout_note(entry_date: str, note: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM workout_log WHERE date = ?", (entry_date,)
        )
        row = await cursor.fetchone()
        if row:
            await db.execute(
                "UPDATE workout_log SET note = ?, updated_at = ? WHERE date = ?",
                (note, now, entry_date),
            )
        else:
            await db.execute(
                "INSERT INTO workout_log (date, completed, note, updated_at) VALUES (?, 0, ?, ?)",
                (entry_date, note, now),
            )
        await db.commit()
        cur = await db.execute("SELECT * FROM workout_log WHERE date = ?", (entry_date,))
        r = await cur.fetchone()
        return dict(r)
    finally:
        await db.close()


# --- Mood ---


async def get_mood(entry_date: str) -> dict | None:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM mood_log WHERE date = ?", (entry_date,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await db.close()


async def save_mood(entry_date: str, mood: int) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            """INSERT OR REPLACE INTO mood_log (date, mood, updated_at)
               VALUES (?, ?, ?)""",
            (entry_date, mood, now),
        )
        await db.commit()
        return {"date": entry_date, "mood": mood, "updated_at": now}
    finally:
        await db.close()


# --- Water ---


async def get_water_today(today_str: str) -> int:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT glasses FROM water_log WHERE date = ?", (today_str,))
        row = await cursor.fetchone()
        return row["glasses"] if row else 0
    finally:
        await db.close()


async def increment_water(today_str: str) -> int:
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO water_log (date, glasses) VALUES (?, 1) ON CONFLICT(date) DO UPDATE SET glasses = glasses + 1",
            (today_str,),
        )
        await db.commit()
        cursor = await db.execute("SELECT glasses FROM water_log WHERE date = ?", (today_str,))
        row = await cursor.fetchone()
        return row["glasses"]
    finally:
        await db.close()


async def decrement_water(today_str: str) -> int:
    db = await get_db()
    try:
        await db.execute(
            "UPDATE water_log SET glasses = MAX(0, glasses - 1) WHERE date = ?",
            (today_str,),
        )
        await db.commit()
        cursor = await db.execute("SELECT glasses FROM water_log WHERE date = ?", (today_str,))
        row = await cursor.fetchone()
        return row["glasses"] if row else 0
    finally:
        await db.close()


async def set_water(today_str: str, glasses: int) -> int:
    glasses = max(0, min(glasses, 20))
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO water_log (date, glasses) VALUES (?, ?) ON CONFLICT(date) DO UPDATE SET glasses = ?",
            (today_str, glasses, glasses),
        )
        await db.commit()
        return glasses
    finally:
        await db.close()


async def get_water_week() -> list[dict]:
    today = date.today()
    start = (today - timedelta(days=6)).isoformat()
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT date, glasses FROM water_log WHERE date >= ? ORDER BY date",
            (start,),
        )
        rows = await cursor.fetchall()
        return [{"date": r["date"], "glasses": r["glasses"]} for r in rows]
    finally:
        await db.close()
