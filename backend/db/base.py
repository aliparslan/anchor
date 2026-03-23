import aiosqlite
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"
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

            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY,
                text TEXT NOT NULL,
                completed_at TEXT,
                position INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                date TEXT NOT NULL
            );
        """)
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.executescript("""
            CREATE INDEX IF NOT EXISTS idx_pomodoro_date ON pomodoro_sessions(date);
            CREATE INDEX IF NOT EXISTS idx_rss_published ON rss_items(published_at DESC);
            CREATE INDEX IF NOT EXISTS idx_habit_completions_date ON habit_completions(date);
            CREATE INDEX IF NOT EXISTS idx_sleep_log_date ON sleep_log(date);
            CREATE INDEX IF NOT EXISTS idx_workout_log_date ON workout_log(date);
            CREATE INDEX IF NOT EXISTS idx_mood_log_date ON mood_log(date);
            CREATE INDEX IF NOT EXISTS idx_journal_entries_date ON journal_entries(date);
            CREATE INDEX IF NOT EXISTS idx_daily_mit_date ON daily_mit(date);
            CREATE INDEX IF NOT EXISTS idx_todos_date ON todos(date);
        """)
        await db.commit()
    finally:
        await db.close()
