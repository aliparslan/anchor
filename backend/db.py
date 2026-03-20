import aiosqlite
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "base.db"


async def get_db() -> aiosqlite.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS hn_posts (
                id INTEGER PRIMARY KEY,
                hn_id INTEGER UNIQUE,
                title TEXT NOT NULL,
                url TEXT,
                domain TEXT,
                score INTEGER,
                comments INTEGER,
                hn_url TEXT,
                fetched_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS youtube_videos (
                id INTEGER PRIMARY KEY,
                video_id TEXT UNIQUE,
                title TEXT NOT NULL,
                channel TEXT,
                thumbnail TEXT,
                duration_seconds INTEGER,
                duration_label TEXT,
                fetched_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS journal_entries (
                date TEXT PRIMARY KEY,
                content TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL DEFAULT 25
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS habit_completions (
                date TEXT NOT NULL,
                habit TEXT NOT NULL,
                PRIMARY KEY (date, habit)
            );

            CREATE TABLE IF NOT EXISTS dismissed_videos (
                video_id TEXT PRIMARY KEY,
                dismissed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id INTEGER PRIMARY KEY,
                endpoint TEXT UNIQUE NOT NULL,
                p256dh TEXT NOT NULL,
                auth TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS daily_mit (
                date TEXT PRIMARY KEY,
                text TEXT NOT NULL DEFAULT '',
                completed INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reading_queue (
                id INTEGER PRIMARY KEY,
                hn_id INTEGER,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                domain TEXT,
                saved_at TEXT NOT NULL,
                read_at TEXT
            );

            CREATE TABLE IF NOT EXISTS sleep_log (
                date TEXT PRIMARY KEY,
                bedtime TEXT,
                wake_time TEXT,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS workout_log (
                date TEXT PRIMARY KEY,
                completed INTEGER NOT NULL DEFAULT 0,
                note TEXT DEFAULT '',
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS mood_log (
                date TEXT PRIMARY KEY,
                mood INTEGER NOT NULL CHECK(mood BETWEEN 1 AND 5),
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quick_capture (
                id INTEGER PRIMARY KEY,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                archived_at TEXT
            );

            CREATE TABLE IF NOT EXISTS custom_habits (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS rss_feeds (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                feed_url TEXT NOT NULL UNIQUE,
                site_url TEXT,
                last_fetched_at TEXT
            );

            CREATE TABLE IF NOT EXISTS rss_items (
                id INTEGER PRIMARY KEY,
                feed_id INTEGER NOT NULL REFERENCES rss_feeds(id),
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                author TEXT,
                published_at TEXT,
                fetched_at TEXT NOT NULL,
                guid TEXT UNIQUE
            );

            CREATE TABLE IF NOT EXISTS water_log (
                date TEXT PRIMARY KEY,
                glasses INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS gratitude_jar (
                id INTEGER PRIMARY KEY,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                earned_at TEXT NOT NULL
            );
        """)
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.executescript("""
            CREATE INDEX IF NOT EXISTS idx_pomodoro_date ON pomodoro_sessions(date);
            CREATE INDEX IF NOT EXISTS idx_rss_published ON rss_items(published_at DESC);
            CREATE INDEX IF NOT EXISTS idx_capture_archived ON quick_capture(archived_at);
        """)
        await db.commit()
    finally:
        await db.close()


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


# --- Daily MIT ---


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


# --- Sleep Log ---


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


# --- Workout Log ---


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


# --- Mood Log ---


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


# --- Quick Capture ---


async def get_captures() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM quick_capture WHERE archived_at IS NULL ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def save_capture(text: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO quick_capture (text, created_at) VALUES (?, ?)",
            (text, now),
        )
        await db.commit()
        item_id = cursor.lastrowid
        return {"id": item_id, "text": text, "created_at": now, "archived_at": None}
    finally:
        await db.close()


async def archive_capture(capture_id: int):
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        await db.execute(
            "UPDATE quick_capture SET archived_at = ? WHERE id = ?", (now, capture_id)
        )
        await db.commit()
    finally:
        await db.close()


async def delete_capture(capture_id: int):
    db = await get_db()
    try:
        await db.execute("DELETE FROM quick_capture WHERE id = ?", (capture_id,))
        await db.commit()
    finally:
        await db.close()


# --- Custom Habits ---


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


# --- Aggregation ---


async def get_habits_week(today: str) -> dict:
    today_date = date.fromisoformat(today)
    dates = [(today_date - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]

    db = await get_db()
    try:
        habits = {
            "focus": [],
            "workout": [],
            "night_routine": [],
            "sleep_tracked": [],
            "mood_logged": [],
        }
        for d in dates:
            # focus: pomodoro total >= 240
            cursor = await db.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?",
                (d,),
            )
            row = await cursor.fetchone()
            habits["focus"].append(int(row["total"]) >= 240)

            # workout
            cursor = await db.execute(
                "SELECT completed FROM workout_log WHERE date = ?", (d,)
            )
            row = await cursor.fetchone()
            habits["workout"].append(bool(row and row["completed"]))

            # night_routine
            cursor = await db.execute(
                "SELECT 1 FROM habit_completions WHERE date = ? AND habit = 'night_routine'",
                (d,),
            )
            row = await cursor.fetchone()
            habits["night_routine"].append(row is not None)

            # sleep_tracked
            cursor = await db.execute(
                "SELECT 1 FROM sleep_log WHERE date = ?", (d,)
            )
            row = await cursor.fetchone()
            habits["sleep_tracked"].append(row is not None)

            # mood_logged
            cursor = await db.execute(
                "SELECT 1 FROM mood_log WHERE date = ?", (d,)
            )
            row = await cursor.fetchone()
            habits["mood_logged"].append(row is not None)

        # Custom habits
        cursor = await db.execute("SELECT * FROM custom_habits ORDER BY created_at")
        custom_rows = await cursor.fetchall()
        for ch in custom_rows:
            habit_key = f"custom:{ch['name']}"
            habits[habit_key] = []
            for d in dates:
                cursor = await db.execute(
                    "SELECT 1 FROM habit_completions WHERE date = ? AND habit = ?",
                    (d, ch["name"]),
                )
                row = await cursor.fetchone()
                habits[habit_key].append(row is not None)

        return {"dates": dates, "habits": habits}
    finally:
        await db.close()


async def get_streaks(today: str) -> dict[str, int]:
    today_date = date.fromisoformat(today)
    db = await get_db()
    try:
        streaks = {}
        habit_checks = {
            "focus": "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?",
            "workout": "SELECT completed FROM workout_log WHERE date = ?",
            "night_routine": "SELECT 1 as v FROM habit_completions WHERE date = ? AND habit = 'night_routine'",
            "sleep_tracked": "SELECT 1 as v FROM sleep_log WHERE date = ?",
            "mood_logged": "SELECT 1 as v FROM mood_log WHERE date = ?",
        }
        for habit_name, query in habit_checks.items():
            count = 0
            d = today_date
            while True:
                ds = d.isoformat()
                cursor = await db.execute(query, (ds,))
                row = await cursor.fetchone()
                done = False
                if habit_name == "focus":
                    done = row is not None and int(row["total"]) >= 240
                elif habit_name == "workout":
                    done = row is not None and bool(row["completed"])
                else:
                    done = row is not None
                if done:
                    count += 1
                    d -= timedelta(days=1)
                else:
                    break
            streaks[habit_name] = count

        # Custom habit streaks
        cursor = await db.execute("SELECT * FROM custom_habits ORDER BY created_at")
        custom_rows = await cursor.fetchall()
        for ch in custom_rows:
            habit_key = f"custom:{ch['name']}"
            count = 0
            d = today_date
            while True:
                ds = d.isoformat()
                cursor = await db.execute(
                    "SELECT 1 FROM habit_completions WHERE date = ? AND habit = ?",
                    (ds, ch["name"]),
                )
                row = await cursor.fetchone()
                if row is not None:
                    count += 1
                    d -= timedelta(days=1)
                else:
                    break
            streaks[habit_key] = count

        return streaks
    finally:
        await db.close()


async def get_daily_summary(today: str) -> dict:
    db = await get_db()
    try:
        # MIT
        cursor = await db.execute(
            "SELECT text, completed FROM daily_mit WHERE date = ?", (today,)
        )
        mit_row = await cursor.fetchone()
        mit = {"text": mit_row["text"], "completed": bool(mit_row["completed"])} if mit_row else None

        # Focus minutes
        cursor = await db.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?",
            (today,),
        )
        row = await cursor.fetchone()
        focus_minutes = int(row["total"])

        # Habits
        cursor = await db.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?",
            (today,),
        )
        pom = await cursor.fetchone()
        focus_done = int(pom["total"]) >= 240

        cursor = await db.execute(
            "SELECT completed FROM workout_log WHERE date = ?", (today,)
        )
        w_row = await cursor.fetchone()
        workout_done = bool(w_row and w_row["completed"])

        cursor = await db.execute(
            "SELECT 1 FROM habit_completions WHERE date = ? AND habit = 'night_routine'",
            (today,),
        )
        nr_row = await cursor.fetchone()
        nr_done = nr_row is not None

        cursor = await db.execute(
            "SELECT 1 FROM sleep_log WHERE date = ?", (today,)
        )
        sl_row = await cursor.fetchone()
        sleep_tracked = sl_row is not None

        cursor = await db.execute(
            "SELECT 1 FROM mood_log WHERE date = ?", (today,)
        )
        ml_row = await cursor.fetchone()
        mood_logged = ml_row is not None

        habits_list = [
            {"name": "focus", "done": focus_done},
            {"name": "workout", "done": workout_done},
            {"name": "night_routine", "done": nr_done},
            {"name": "sleep_tracked", "done": sleep_tracked},
            {"name": "mood_logged", "done": mood_logged},
        ]

        # Custom habits
        cursor = await db.execute("SELECT * FROM custom_habits ORDER BY created_at")
        custom_rows = await cursor.fetchall()
        for ch in custom_rows:
            cursor = await db.execute(
                "SELECT 1 FROM habit_completions WHERE date = ? AND habit = ?",
                (today, ch["name"]),
            )
            ch_row = await cursor.fetchone()
            habits_list.append({"name": f"custom:{ch['name']}", "done": ch_row is not None})

        # Journal
        cursor = await db.execute(
            "SELECT 1 FROM journal_entries WHERE date = ? AND content != ''", (today,)
        )
        j_row = await cursor.fetchone()
        journal_written = j_row is not None

        # Mood
        cursor = await db.execute(
            "SELECT mood FROM mood_log WHERE date = ?", (today,)
        )
        mood_row = await cursor.fetchone()
        mood_val = mood_row["mood"] if mood_row else None

        # Sleep
        cursor = await db.execute(
            "SELECT bedtime, wake_time FROM sleep_log WHERE date = ?", (today,)
        )
        sleep_row = await cursor.fetchone()
        sleep_data = {"bedtime": sleep_row["bedtime"], "wake_time": sleep_row["wake_time"]} if sleep_row else None

        # Workout
        cursor = await db.execute(
            "SELECT completed, note FROM workout_log WHERE date = ?", (today,)
        )
        wo_row = await cursor.fetchone()
        workout_data = {"completed": bool(wo_row["completed"]), "note": wo_row["note"]} if wo_row else None

        return {
            "mit": mit,
            "focus_minutes": focus_minutes,
            "habits": habits_list,
            "journal_written": journal_written,
            "mood": mood_val,
            "sleep": sleep_data,
            "workout": workout_data,
        }
    finally:
        await db.close()


async def get_focus_month(today_str: str) -> list[dict]:
    """Get daily focus minutes for last 30 days."""
    today = date.fromisoformat(today_str)
    start = (today - timedelta(days=29)).isoformat()
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT date, COALESCE(SUM(duration_minutes), 0) as minutes
               FROM pomodoro_sessions
               WHERE date >= ? AND date <= ?
               GROUP BY date
               ORDER BY date ASC""",
            (start, today_str),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


async def get_streak(today_str: str) -> int:
    """Count consecutive days with all core tasks done."""
    db = await get_db()
    try:
        streak = 0
        current = date.fromisoformat(today_str)
        while True:
            d = current.isoformat()
            # MIT completed
            mit = await db.execute("SELECT completed FROM daily_mit WHERE date = ?", (d,))
            mit_row = await mit.fetchone()
            if not mit_row or not mit_row["completed"]:
                break
            # Focus >= 240 min
            pom = await db.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?", (d,)
            )
            pom_row = await pom.fetchone()
            if pom_row["total"] < 240:
                break
            # Journal written
            j = await db.execute("SELECT content FROM journal_entries WHERE date = ?", (d,))
            j_row = await j.fetchone()
            if not j_row or not j_row["content"].strip():
                break
            streak += 1
            current -= timedelta(days=1)
        return streak
    finally:
        await db.close()


async def get_daily_score(today_str: str) -> dict:
    """Compute daily score 0-100."""
    db = await get_db()
    try:
        score = 0
        breakdown = {}

        # MIT: 25 pts
        mit = await db.execute("SELECT completed FROM daily_mit WHERE date = ?", (today_str,))
        mit_row = await mit.fetchone()
        mit_pts = 25 if (mit_row and mit_row["completed"]) else 0
        breakdown["mit"] = mit_pts
        score += mit_pts

        # Focus: 25 pts (proportional to 240 min)
        pom = await db.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?",
            (today_str,),
        )
        pom_row = await pom.fetchone()
        focus_mins = pom_row["total"]
        focus_pts = min(25, round(focus_mins / 240 * 25))
        breakdown["focus"] = focus_pts
        score += focus_pts

        # Habits: 25 pts (proportional) — count ALL habits including auto-tracked
        done_habits = 0
        total_habits = 5  # focus, workout, night_routine, sleep_tracked, mood_logged

        # Auto: focus achieved (>= 240 min)
        if focus_mins >= 240:
            done_habits += 1
        # Auto: workout
        wo = await db.execute("SELECT completed FROM workout_log WHERE date = ?", (today_str,))
        wo_row = await wo.fetchone()
        if wo_row and wo_row["completed"]:
            done_habits += 1
        # Manual: night_routine (in habit_completions)
        nr = await db.execute("SELECT 1 FROM habit_completions WHERE date = ? AND habit = 'night_routine'", (today_str,))
        if await nr.fetchone():
            done_habits += 1
        # Auto: sleep tracked
        sl = await db.execute("SELECT 1 FROM sleep_log WHERE date = ?", (today_str,))
        if await sl.fetchone():
            done_habits += 1
        # Auto: mood logged
        mood_check = await db.execute("SELECT 1 FROM mood_log WHERE date = ?", (today_str,))
        if await mood_check.fetchone():
            done_habits += 1
        # Custom habits
        custom_cursor = await db.execute("SELECT COUNT(*) as c FROM custom_habits")
        custom_row = await custom_cursor.fetchone()
        total_habits += custom_row["c"]
        custom_done = await db.execute(
            "SELECT COUNT(*) as c FROM habit_completions WHERE date = ? AND habit != 'night_routine'", (today_str,)
        )
        custom_done_row = await custom_done.fetchone()
        done_habits += custom_done_row["c"]

        habit_pts = min(25, round(done_habits / max(total_habits, 1) * 25))
        breakdown["habits"] = habit_pts
        score += habit_pts

        # Journal: 15 pts
        j = await db.execute("SELECT content FROM journal_entries WHERE date = ?", (today_str,))
        j_row = await j.fetchone()
        journal_pts = 15 if (j_row and j_row["content"].strip()) else 0
        breakdown["journal"] = journal_pts
        score += journal_pts

        # Mood: 10 pts
        m = await db.execute("SELECT mood FROM mood_log WHERE date = ?", (today_str,))
        m_row = await m.fetchone()
        mood_pts = 10 if m_row else 0
        breakdown["mood"] = mood_pts
        score += mood_pts

        return {"score": score, "breakdown": breakdown}
    finally:
        await db.close()


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


async def get_weekly_review(today: str) -> dict:
    today_date = date.fromisoformat(today)
    dates = [(today_date - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    start_date = dates[0]
    end_date = dates[-1]

    db = await get_db()
    try:
        # Focus hours
        cursor = await db.execute(
            "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date >= ? AND date <= ?",
            (start_date, end_date),
        )
        row = await cursor.fetchone()
        focus_hours = round(int(row["total"]) / 60, 1)

        # Habit rate
        completed_count = 0
        total_count = 5 * 7
        for d in dates:
            cursor = await db.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?",
                (d,),
            )
            r = await cursor.fetchone()
            if int(r["total"]) >= 240:
                completed_count += 1

            cursor = await db.execute(
                "SELECT completed FROM workout_log WHERE date = ?", (d,)
            )
            r = await cursor.fetchone()
            if r and r["completed"]:
                completed_count += 1

            cursor = await db.execute(
                "SELECT 1 FROM habit_completions WHERE date = ? AND habit = 'night_routine'",
                (d,),
            )
            if await cursor.fetchone():
                completed_count += 1

            cursor = await db.execute(
                "SELECT 1 FROM sleep_log WHERE date = ?", (d,)
            )
            if await cursor.fetchone():
                completed_count += 1

            cursor = await db.execute(
                "SELECT 1 FROM mood_log WHERE date = ?", (d,)
            )
            if await cursor.fetchone():
                completed_count += 1

        # Mood trend
        mood_trend = []
        for d in dates:
            cursor = await db.execute(
                "SELECT mood FROM mood_log WHERE date = ?", (d,)
            )
            r = await cursor.fetchone()
            mood_trend.append(r["mood"] if r else None)

        # MIT rate
        cursor = await db.execute(
            "SELECT COUNT(*) as total FROM daily_mit WHERE date >= ? AND date <= ?",
            (start_date, end_date),
        )
        r = await cursor.fetchone()
        mit_total = int(r["total"])

        cursor = await db.execute(
            "SELECT COUNT(*) as total FROM daily_mit WHERE date >= ? AND date <= ? AND completed = 1",
            (start_date, end_date),
        )
        r = await cursor.fetchone()
        mit_completed = int(r["total"])

        # Avg sleep hours
        cursor = await db.execute(
            "SELECT bedtime, wake_time FROM sleep_log WHERE date >= ? AND date <= ?",
            (start_date, end_date),
        )
        sleep_rows = await cursor.fetchall()
        avg_sleep = None
        if sleep_rows:
            total_hours = 0.0
            valid_count = 0
            for sr in sleep_rows:
                try:
                    bt = datetime.strptime(sr["bedtime"], "%H:%M")
                    wt = datetime.strptime(sr["wake_time"], "%H:%M")
                    diff = (wt - bt).total_seconds() / 3600
                    if diff <= 0:
                        diff += 24  # crossed midnight
                    total_hours += diff
                    valid_count += 1
                except (ValueError, TypeError):
                    pass
            if valid_count > 0:
                avg_sleep = round(total_hours / valid_count, 1)

        # Focus per day
        focus_per_day = []
        for d in dates:
            cursor = await db.execute(
                "SELECT COALESCE(SUM(duration_minutes), 0) as total FROM pomodoro_sessions WHERE date = ?",
                (d,),
            )
            r = await cursor.fetchone()
            focus_per_day.append(round(int(r["total"]) / 60, 1))

        return {
            "focus_hours": focus_hours,
            "habit_rate": {"completed": completed_count, "total": total_count},
            "mood_trend": mood_trend,
            "mit_rate": {"completed": mit_completed, "total": mit_total},
            "avg_sleep_hours": avg_sleep,
            "focus_per_day": focus_per_day,
        }
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
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT date, glasses FROM water_log WHERE date >= date('now', '-6 days') ORDER BY date"
        )
        rows = await cursor.fetchall()
        return [{"date": r["date"], "glasses": r["glasses"]} for r in rows]
    finally:
        await db.close()


# --- Gratitude ---


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


# --- Search ---


async def search_all(query: str, limit: int = 20) -> dict:
    db = await get_db()
    q = f"%{query}%"
    try:
        results = {"journal": [], "captures": [], "queue": [], "rss": []}
        # Journal
        cur = await db.execute(
            "SELECT date, content FROM journal_entries WHERE content LIKE ? ORDER BY date DESC LIMIT ?",
            (q, limit),
        )
        results["journal"] = [dict(r) for r in await cur.fetchall()]
        # Captures
        cur = await db.execute(
            "SELECT id, text, created_at FROM quick_capture WHERE text LIKE ? AND archived_at IS NULL ORDER BY created_at DESC LIMIT ?",
            (q, limit),
        )
        results["captures"] = [dict(r) for r in await cur.fetchall()]
        # Reading queue
        cur = await db.execute(
            "SELECT id, title, url, domain FROM reading_queue WHERE title LIKE ? ORDER BY saved_at DESC LIMIT ?",
            (q, limit),
        )
        results["queue"] = [dict(r) for r in await cur.fetchall()]
        # RSS items
        cur = await db.execute(
            "SELECT ri.id, ri.title, ri.url, rf.name as feed_name FROM rss_items ri JOIN rss_feeds rf ON ri.feed_id = rf.id WHERE ri.title LIKE ? ORDER BY ri.published_at DESC LIMIT ?",
            (q, limit),
        )
        results["rss"] = [dict(r) for r in await cur.fetchall()]
        return results
    finally:
        await db.close()


# --- Achievements ---


async def get_achievements() -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM achievements ORDER BY earned_at DESC")
        return [dict(row) for row in await cursor.fetchall()]
    finally:
        await db.close()


async def award_achievement(name: str, description: str) -> bool:
    """Award achievement if not already earned. Returns True if newly awarded."""
    db = await get_db()
    try:
        existing = await db.execute("SELECT id FROM achievements WHERE name = ?", (name,))
        if await existing.fetchone():
            return False
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO achievements (name, description, earned_at) VALUES (?, ?, ?)",
            (name, description, now),
        )
        await db.commit()
        return True
    finally:
        await db.close()


async def check_achievements(today_str: str) -> list[dict]:
    """Check and award any new achievements. Returns newly awarded ones."""
    db = await get_db()
    newly_awarded = []
    try:
        # Total pomodoros
        cur = await db.execute("SELECT COUNT(*) as c FROM pomodoro_sessions")
        total_pomos = (await cur.fetchone())["c"]
        if total_pomos >= 1:
            if await award_achievement("first_pomodoro", "Completed your first focus session"):
                newly_awarded.append({"name": "first_pomodoro", "description": "Completed your first focus session"})
        if total_pomos >= 10:
            if await award_achievement("10_pomodoros", "Completed 10 focus sessions"):
                newly_awarded.append({"name": "10_pomodoros", "description": "Completed 10 focus sessions"})
        if total_pomos >= 100:
            if await award_achievement("100_pomodoros", "Completed 100 focus sessions"):
                newly_awarded.append({"name": "100_pomodoros", "description": "Completed 100 focus sessions"})

        # Journal entries
        cur = await db.execute("SELECT COUNT(*) as c FROM journal_entries WHERE content != ''")
        total_journal = (await cur.fetchone())["c"]
        if total_journal >= 1:
            if await award_achievement("first_journal", "Wrote your first journal entry"):
                newly_awarded.append({"name": "first_journal", "description": "Wrote your first journal entry"})
        if total_journal >= 30:
            if await award_achievement("30_journals", "Wrote 30 journal entries"):
                newly_awarded.append({"name": "30_journals", "description": "Wrote 30 journal entries"})

        # Reading queue
        cur = await db.execute("SELECT COUNT(*) as c FROM reading_queue")
        total_saved = (await cur.fetchone())["c"]
        if total_saved >= 50:
            if await award_achievement("50_saved", "Saved 50 articles to reading queue"):
                newly_awarded.append({"name": "50_saved", "description": "Saved 50 articles to reading queue"})

        # Inbox zero
        cur = await db.execute("SELECT COUNT(*) as c FROM reading_queue WHERE read_at IS NULL")
        unread = (await cur.fetchone())["c"]
        cur2 = await db.execute("SELECT COUNT(*) as c FROM quick_capture WHERE archived_at IS NULL")
        uncaptured = (await cur2.fetchone())["c"]
        if total_saved > 0 and unread == 0 and uncaptured == 0:
            if await award_achievement("inbox_zero", "Achieved inbox zero"):
                newly_awarded.append({"name": "inbox_zero", "description": "Achieved inbox zero"})

        return newly_awarded
    finally:
        await db.close()
