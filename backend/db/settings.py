from datetime import datetime, timezone

from db.base import get_db


async def get_setting(key: str) -> str | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row["value"] if row else None
    finally:
        await db.close()


async def save_setting(key: str, value: str):
    db = await get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        await db.commit()
    finally:
        await db.close()


async def save_push_subscription(endpoint: str, p256dh: str, auth: str):
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            """INSERT OR REPLACE INTO push_subscriptions (endpoint, p256dh, auth, created_at)
               VALUES (?, ?, ?, ?)""",
            (endpoint, p256dh, auth, now),
        )
        await db.commit()
    finally:
        await db.close()


async def delete_push_subscription(endpoint: str):
    db = await get_db()
    try:
        await db.execute("DELETE FROM push_subscriptions WHERE endpoint = ?", (endpoint,))
        await db.commit()
    finally:
        await db.close()


async def get_push_subscriptions() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT endpoint, p256dh, auth FROM push_subscriptions")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()
