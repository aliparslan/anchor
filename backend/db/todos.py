from datetime import date, datetime, timezone

from db.base import get_db


async def get_todos() -> list[dict]:
    """Get today's active todos + today's completed todos.
    Active todos sorted by position ASC.
    Completed todos sorted by completed_at DESC.
    Excludes completed todos from before today."""
    today = date.today().isoformat()
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM todos WHERE completed_at IS NULL ORDER BY position ASC"
        )
        active = await cursor.fetchall()
        cursor = await db.execute(
            "SELECT * FROM todos WHERE completed_at IS NOT NULL AND date = ? ORDER BY completed_at DESC",
            (today,),
        )
        completed = await cursor.fetchall()
        return [dict(r) for r in active] + [dict(r) for r in completed]
    finally:
        await db.close()


async def create_todo(text: str) -> dict:
    """Create a new todo. Set date to today, position to max+1, created_at to now UTC."""
    today = date.today().isoformat()
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT COALESCE(MAX(position), 0) + 1 AS next_pos FROM todos WHERE completed_at IS NULL"
        )
        row = await cursor.fetchone()
        position = row["next_pos"]
        cursor = await db.execute(
            "INSERT INTO todos (text, position, created_at, date) VALUES (?, ?, ?, ?)",
            (text, position, now, today),
        )
        await db.commit()
        todo_id = cursor.lastrowid
        cursor = await db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        todo = await cursor.fetchone()
        return dict(todo)
    finally:
        await db.close()


async def update_todo(todo_id: int, text: str) -> dict:
    """Update todo text."""
    db = await get_db()
    try:
        await db.execute("UPDATE todos SET text = ? WHERE id = ?", (text, todo_id))
        await db.commit()
        cursor = await db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        todo = await cursor.fetchone()
        return dict(todo)
    finally:
        await db.close()


async def complete_todo(todo_id: int) -> dict:
    """Set completed_at to now UTC."""
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            "UPDATE todos SET completed_at = ? WHERE id = ?", (now, todo_id)
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        todo = await cursor.fetchone()
        return dict(todo)
    finally:
        await db.close()


async def undo_todo(todo_id: int) -> dict:
    """Clear completed_at."""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE todos SET completed_at = NULL WHERE id = ?", (todo_id,)
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        todo = await cursor.fetchone()
        return dict(todo)
    finally:
        await db.close()


async def delete_todo(todo_id: int):
    """Delete a todo."""
    db = await get_db()
    try:
        await db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        await db.commit()
    finally:
        await db.close()


async def reorder_todos(ids: list[int]):
    """Update position for each todo based on order in the ids list."""
    db = await get_db()
    try:
        for position, todo_id in enumerate(ids):
            await db.execute(
                "UPDATE todos SET position = ? WHERE id = ?", (position, todo_id)
            )
        await db.commit()
    finally:
        await db.close()
