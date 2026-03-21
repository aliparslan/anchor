from datetime import datetime, timezone

from db.base import get_db


async def get_habit_completions(entry_date: str) -> list[str]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT habit FROM habit_completions WHERE date = ?", (entry_date,)
        )
        rows = await cursor.fetchall()
        return [row["habit"] for row in rows]
    finally:
        await db.close()


async def toggle_habit(entry_date: str, habit: str) -> bool:
    db = await get_db()
    try:
        async with db.execute("BEGIN"):
            cursor = await db.execute(
                "SELECT 1 FROM habit_completions WHERE date = ? AND habit = ?",
                (entry_date, habit),
            )
            exists = await cursor.fetchone()
            if exists:
                await db.execute(
                    "DELETE FROM habit_completions WHERE date = ? AND habit = ?",
                    (entry_date, habit),
                )
                await db.commit()
                return False
            else:
                await db.execute(
                    "INSERT INTO habit_completions (date, habit) VALUES (?, ?)",
                    (entry_date, habit),
                )
                await db.commit()
                return True
    finally:
        await db.close()


async def get_custom_habits() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM custom_habits ORDER BY created_at"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def add_custom_habit(name: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO custom_habits (name, created_at) VALUES (?, ?)",
            (name, now),
        )
        await db.commit()
        habit_id = cursor.lastrowid
        return {"id": habit_id, "name": name, "created_at": now}
    finally:
        await db.close()


async def delete_custom_habit(habit_id: int):
    db = await get_db()
    try:
        # Get the habit name first so we can clean up completions
        cursor = await db.execute(
            "SELECT name FROM custom_habits WHERE id = ?", (habit_id,)
        )
        row = await cursor.fetchone()
        if row:
            await db.execute(
                "DELETE FROM habit_completions WHERE habit = ?", (row["name"],)
            )
        await db.execute("DELETE FROM custom_habits WHERE id = ?", (habit_id,))
        await db.commit()
    finally:
        await db.close()
