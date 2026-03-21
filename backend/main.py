import aiohttp
import asyncio
import base64
from contextlib import asynccontextmanager
from datetime import date
import json
from pathlib import Path
import platform
import time

import psutil

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pywebpush import webpush, WebPushException
from py_vapid import Vapid

from db import (
    init_db,
    get_latest_hn_posts,
    get_latest_youtube_videos,
    get_journal_dates,
    get_journal_entries_preview,
    get_journal_entry,
    save_journal_entry,
    get_pomodoro_sessions,
    save_pomodoro_session,
    get_setting,
    save_setting,
    save_push_subscription,
    delete_push_subscription,
    get_push_subscriptions,
    dismiss_video,
    get_dismissed_video_ids,
    get_habit_completions,
    toggle_habit,
    get_pomodoro_total,
    get_mit,
    save_mit,
    toggle_mit,
    get_reading_queue,
    save_to_reading_queue,
    mark_queue_item_read,
    delete_queue_item,
    delete_queue_item_by_hn_id,
    mark_queue_item_unread,
    get_sleep_log,
    save_sleep_log,
    get_sleep_week,
    get_workout,
    toggle_workout,
    save_workout_note,
    get_mood,
    save_mood,
    get_captures,
    save_capture,
    archive_capture,
    delete_capture,
    get_habits_week,
    get_streaks,
    get_daily_summary,
    get_weekly_review,
    get_custom_habits,
    add_custom_habit,
    delete_custom_habit,
    get_focus_month,
    get_streak,
    get_daily_score,
    seed_rss_feeds,
    get_rss_items,
    get_water_today,
    increment_water,
    decrement_water,
    set_water,
    get_water_week,
    get_gratitudes,
    save_gratitude,
    get_random_gratitude,
    search_all,
    get_achievements,
    check_achievements,
)
from hn import fetch_top_hn_posts
from youtube import fetch_youtube_recommendations
from rss import fetch_all_feeds
from weather import geocode_zip, fetch_weather

VAPID_PRIVATE_KEY: str | None = None
VAPID_PUBLIC_KEY: str | None = None


async def load_or_create_vapid_keys():
    global VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY
    private_pem = await get_setting("vapid_private_key")
    public_b64 = await get_setting("vapid_public_key")
    if private_pem and public_b64:
        VAPID_PRIVATE_KEY = private_pem
        VAPID_PUBLIC_KEY = public_b64
        print("[Push] Loaded existing VAPID keys")
        return
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    public_b64 = base64.urlsafe_b64encode(public_bytes).rstrip(b"=").decode()
    await save_setting("vapid_private_key", private_pem)
    await save_setting("vapid_public_key", public_b64)
    VAPID_PRIVATE_KEY = private_pem
    VAPID_PUBLIC_KEY = public_b64
    print("[Push] Generated new VAPID keys")


async def send_push_to_all(title: str, body: str):
    if not VAPID_PRIVATE_KEY:
        return
    subs = await get_push_subscriptions()
    if not subs:
        return
    payload = json.dumps({"title": title, "body": body})
    vapid = Vapid.from_pem(VAPID_PRIVATE_KEY.encode())
    loop = asyncio.get_event_loop()
    for sub in subs:
        try:
            await loop.run_in_executor(None, lambda s=sub: webpush(
                subscription_info={
                    "endpoint": s["endpoint"],
                    "keys": {"p256dh": s["p256dh"], "auth": s["auth"]},
                },
                data=payload,
                vapid_private_key=vapid,
                vapid_claims={"sub": "mailto:noreply@base.local"},
            ))
        except WebPushException as e:
            print(f"[Push] Failed to send to {sub['endpoint'][:40]}...: {e}")
            if e.response and e.response.status_code in (404, 410):
                await delete_push_subscription(sub["endpoint"])


class JournalBody(BaseModel):
    content: str


class ZipBody(BaseModel):
    zip_code: str


class PushSubscriptionBody(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


class MitBody(BaseModel):
    text: str


class ReadingQueueBody(BaseModel):
    hn_id: int | None = None
    title: str
    url: str
    domain: str | None = None


class WaterSetBody(BaseModel):
    glasses: int


class SleepBody(BaseModel):
    bedtime: str
    wake_time: str


class WorkoutNoteBody(BaseModel):
    note: str


class MoodBody(BaseModel):
    mood: int = Field(ge=1, le=5)


class CaptureBody(BaseModel):
    text: str


class GratitudeBody(BaseModel):
    text: str


class CustomHabitBody(BaseModel):
    name: str = Field(min_length=1, max_length=100)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "build"

scheduler = AsyncIOScheduler()


async def scheduled_fetch(notify: bool = True):
    print("[Scheduler] Running scheduled fetch...")
    results = await asyncio.gather(
        fetch_top_hn_posts(),
        fetch_youtube_recommendations(count=30),
        fetch_all_feeds(),
        return_exceptions=True,
    )
    for name, result in zip(["HN", "YouTube", "RSS"], results):
        if isinstance(result, Exception):
            print(f"[Scheduler] {name} fetch failed: {result}")
    if notify:
        await send_push_to_all("Base", "New content ready")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("[Base] Database initialized")
    await load_or_create_vapid_keys()
    await seed_rss_feeds()

    # Run initial fetch in background (no notification on startup)
    asyncio.create_task(scheduled_fetch(notify=False))

    # Schedule twice daily: 8am and 6pm
    scheduler.add_job(scheduled_fetch, "cron", hour="8,18", minute=0)
    scheduler.start()
    print("[Base] Scheduler started (8am, 6pm)")

    yield

    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/hn")
async def api_hn():
    posts = await get_latest_hn_posts()
    return {"posts": posts}


@app.get("/api/youtube")
async def api_youtube():
    videos = await get_latest_youtube_videos(limit=30)
    return {"videos": videos}


@app.post("/api/refresh/hn")
async def refresh_hn():
    posts = await fetch_top_hn_posts()
    return {"posts": posts, "refreshed": True}


@app.post("/api/refresh/youtube")
async def refresh_youtube():
    videos = await fetch_youtube_recommendations(count=30)
    return {"videos": videos, "refreshed": True}


@app.get("/api/rss")
async def api_rss():
    items = await get_rss_items(limit=50)
    return {"items": items}


@app.post("/api/refresh/rss")
async def api_refresh_rss():
    await fetch_all_feeds()
    items = await get_rss_items(limit=50)
    return {"items": items, "refreshed": True}


@app.get("/api/journal/dates")
async def api_journal_dates():
    dates = await get_journal_dates()
    return {"dates": dates}

@app.get("/api/journal/entries")
async def api_journal_entries(limit: int = 20, offset: int = 0):
    entries = await get_journal_entries_preview(limit=limit, offset=offset)
    return {"entries": entries}


@app.get("/api/journal/today")
async def api_journal_today():
    today = date.today().isoformat()
    entry = await get_journal_entry(today)
    return {"entry": entry}


@app.get("/api/journal/{entry_date}")
async def api_journal_by_date(entry_date: str):
    try:
        date.fromisoformat(entry_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format")
    entry = await get_journal_entry(entry_date)
    return {"entry": entry}


@app.put("/api/journal/today")
async def api_save_journal_today(body: JournalBody):
    today = date.today().isoformat()
    entry = await save_journal_entry(today, body.content)
    return {"entry": entry}


@app.put("/api/journal/{entry_date}")
async def api_save_journal(entry_date: str, body: JournalBody):
    try:
        date.fromisoformat(entry_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format")
    entry = await save_journal_entry(entry_date, body.content)
    return {"entry": entry}


@app.get("/api/pomodoro/today")
async def api_pomodoro_today():
    today = date.today().isoformat()
    sessions = await get_pomodoro_sessions(today)
    total_minutes = sum(s["duration_minutes"] for s in sessions)
    return {"sessions": sessions, "total_minutes": total_minutes}


@app.post("/api/pomodoro/complete")
async def api_pomodoro_complete():
    today = date.today().isoformat()
    await save_pomodoro_session(today, 25)
    sessions = await get_pomodoro_sessions(today)
    total_minutes = sum(s["duration_minutes"] for s in sessions)
    return {"sessions": sessions, "total_minutes": total_minutes}


@app.get("/api/weather")
async def api_weather():
    coords_raw = await get_setting("weather_coords")
    zip_code = await get_setting("weather_zip")
    if not coords_raw:
        return {"weather": None, "zip_code": zip_code}
    coords = json.loads(coords_raw)
    weather = await fetch_weather(coords["lat"], coords["lon"])
    return {"weather": weather, "zip_code": zip_code, "location": coords.get("name", "")}


@app.put("/api/weather/zip")
async def api_set_zip(body: ZipBody):
    coords = await geocode_zip(body.zip_code)
    if not coords:
        raise HTTPException(status_code=404, detail="Could not find location")
    await save_setting("weather_zip", body.zip_code)
    await save_setting("weather_coords", json.dumps(coords))
    weather = await fetch_weather(coords["lat"], coords["lon"])
    return {"weather": weather, "zip_code": body.zip_code, "location": coords.get("name", "")}


@app.get("/api/habits/today")
async def api_habits_today():
    today = date.today().isoformat()
    total_minutes, completions, sleep, workout, mood, custom_habits_list = await asyncio.gather(
        get_pomodoro_total(today),
        get_habit_completions(today),
        get_sleep_log(today),
        get_workout(today),
        get_mood(today),
        get_custom_habits(),
    )
    result = {
        "date": today,
        "focus_minutes": total_minutes,
        "focus_achieved": total_minutes >= 240,
        "workout": workout.get("completed", 0) if workout else 0,
        "night_routine": "night_routine" in completions,
        "sleep_tracked": sleep is not None,
        "mood_logged": mood is not None,
        "custom_habits": {},
    }
    for ch in custom_habits_list:
        result["custom_habits"][ch["name"]] = ch["name"] in completions
    return result


@app.post("/api/habits/toggle/{habit}")
async def api_toggle_habit(habit: str):
    today = date.today().isoformat()
    done = await toggle_habit(today, habit)
    return {"done": done}


# --- Custom Habits ---


@app.get("/api/habits/custom")
async def api_custom_habits():
    habits = await get_custom_habits()
    return {"habits": habits}


@app.post("/api/habits/custom")
async def api_add_custom_habit(body: CustomHabitBody):
    habit = await add_custom_habit(body.name)
    return {"habit": habit}


@app.delete("/api/habits/custom/{habit_id}")
async def api_delete_custom_habit(habit_id: int):
    await delete_custom_habit(habit_id)
    return {"ok": True}


@app.get("/api/videos/dismissed")
async def api_dismissed_videos():
    ids = await get_dismissed_video_ids()
    return {"dismissed": ids}


@app.post("/api/videos/dismiss/{video_id}")
async def api_dismiss_video(video_id: str):
    await dismiss_video(video_id)
    return {"ok": True}


@app.get("/api/push/vapid-key")
async def api_vapid_key():
    return {"public_key": VAPID_PUBLIC_KEY}


@app.post("/api/push/subscribe")
async def api_push_subscribe(body: PushSubscriptionBody):
    await save_push_subscription(body.endpoint, body.p256dh, body.auth)
    return {"ok": True}


@app.delete("/api/push/subscribe")
async def api_push_unsubscribe(body: PushSubscriptionBody):
    await delete_push_subscription(body.endpoint)
    return {"ok": True}


@app.post("/api/push/test")
async def api_push_test():
    await send_push_to_all("Base", "Test notification ✦")
    return {"ok": True}


# Timer push notification scheduling
_timer_task: asyncio.Task | None = None


class TimerScheduleBody(BaseModel):
    fire_at: float  # Unix timestamp in seconds
    title: str = "Anchor"
    body: str = "Timer complete!"


@app.post("/api/push/schedule-timer")
async def api_schedule_timer(req: TimerScheduleBody):
    global _timer_task
    if _timer_task and not _timer_task.done():
        _timer_task.cancel()

    async def _fire():
        delay = max(0, req.fire_at - asyncio.get_event_loop().time() + (req.fire_at - time.time()))
        delay = max(0, req.fire_at - time.time())
        await asyncio.sleep(delay)
        await send_push_to_all(req.title, req.body)

    _timer_task = asyncio.create_task(_fire())
    return {"ok": True}


@app.delete("/api/push/schedule-timer")
async def api_cancel_timer():
    global _timer_task
    if _timer_task and not _timer_task.done():
        _timer_task.cancel()
        _timer_task = None
    return {"ok": True}


# --- MIT ---


@app.get("/api/mit/today")
async def api_mit_today():
    today = date.today().isoformat()
    mit = await get_mit(today)
    return {"mit": mit}


@app.put("/api/mit/today")
async def api_save_mit_today(body: MitBody):
    today = date.today().isoformat()
    mit = await save_mit(today, body.text)
    return {"mit": mit}


@app.post("/api/mit/today/toggle")
async def api_toggle_mit_today():
    today = date.today().isoformat()
    completed = await toggle_mit(today)
    return {"completed": completed}


# --- Reading Queue ---


@app.get("/api/reading-queue")
async def api_reading_queue():
    items = await get_reading_queue()
    return {"items": items}


@app.post("/api/reading-queue")
async def api_save_reading_queue(body: ReadingQueueBody):
    item = await save_to_reading_queue(body.hn_id, body.title, body.url, body.domain)
    return {"item": item}


@app.post("/api/reading-queue/{item_id}/read")
async def api_mark_queue_read(item_id: int):
    await mark_queue_item_read(item_id)
    return {"ok": True}


@app.delete("/api/reading-queue/{item_id}")
async def api_delete_queue_item(item_id: int):
    await delete_queue_item(item_id)
    return {"ok": True}


@app.delete("/api/reading-queue/by-hn/{hn_id}")
async def api_delete_queue_by_hn(hn_id: int):
    await delete_queue_item_by_hn_id(hn_id)
    return {"ok": True}


@app.post("/api/reading-queue/{item_id}/unread")
async def api_mark_queue_unread(item_id: int):
    await mark_queue_item_unread(item_id)
    return {"ok": True}


# --- Sleep ---


@app.get("/api/sleep/week")
async def api_sleep_week():
    today = date.today().isoformat()
    days = await get_sleep_week(today)
    return {"days": days}


@app.get("/api/sleep/today")
async def api_sleep_today():
    today = date.today().isoformat()
    sleep = await get_sleep_log(today)
    return {"sleep": sleep}


@app.put("/api/sleep/today")
async def api_save_sleep_today(body: SleepBody):
    today = date.today().isoformat()
    sleep = await save_sleep_log(today, body.bedtime, body.wake_time)
    return {"sleep": sleep}


# --- Workout ---


@app.get("/api/workout/today")
async def api_workout_today():
    today = date.today().isoformat()
    workout = await get_workout(today)
    return {"workout": workout}


@app.post("/api/workout/today/toggle")
async def api_toggle_workout_today():
    today = date.today().isoformat()
    completed = await toggle_workout(today)
    return {"completed": completed}


@app.put("/api/workout/today")
async def api_save_workout_today(body: WorkoutNoteBody):
    today = date.today().isoformat()
    workout = await save_workout_note(today, body.note)
    return {"workout": workout}


# --- Mood ---


@app.get("/api/mood/today")
async def api_mood_today():
    today = date.today().isoformat()
    mood = await get_mood(today)
    return {"mood": mood}


@app.put("/api/mood/today")
async def api_save_mood_today(body: MoodBody):
    today = date.today().isoformat()
    mood = await save_mood(today, body.mood)
    return {"mood": mood}


# --- Quick Capture ---


@app.get("/api/captures")
async def api_captures():
    captures = await get_captures()
    return {"captures": captures}


@app.post("/api/captures")
async def api_save_capture(body: CaptureBody):
    capture = await save_capture(body.text)
    return {"capture": capture}


@app.post("/api/captures/{capture_id}/archive")
async def api_archive_capture(capture_id: int):
    await archive_capture(capture_id)
    return {"ok": True}


@app.delete("/api/captures/{capture_id}")
async def api_delete_capture(capture_id: int):
    await delete_capture(capture_id)
    return {"ok": True}


# --- Aggregation ---


@app.get("/api/summary/today")
async def api_summary_today():
    today = date.today().isoformat()
    return await get_daily_summary(today)


@app.get("/api/habits/week")
async def api_habits_week():
    today = date.today().isoformat()
    return await get_habits_week(today)


@app.get("/api/habits/streaks")
async def api_habits_streaks():
    today = date.today().isoformat()
    streaks = await get_streaks(today)
    return {"streaks": streaks}


@app.get("/api/focus/month")
async def api_focus_month():
    today = date.today().isoformat()
    days = await get_focus_month(today)
    return {"days": days}


@app.get("/api/streak")
async def api_streak():
    today = date.today().isoformat()
    streak = await get_streak(today)
    return {"streak": streak}


@app.get("/api/score/today")
async def api_score_today():
    today = date.today().isoformat()
    return await get_daily_score(today)


@app.get("/api/review/week")
async def api_review_week():
    today = date.today().isoformat()
    return await get_weekly_review(today)


# --- Status ---


@app.get("/api/status/system")
async def api_system_status():
    hostname = platform.node()

    # Uptime
    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    mins = (uptime_seconds % 3600) // 60
    uptime_str = f"{days}d {hours}h {mins}m" if days > 0 else f"{hours}h {mins}m"

    # CPU
    cpu_percent = await asyncio.get_event_loop().run_in_executor(
        None, lambda: psutil.cpu_percent(interval=0.5)
    )

    # Memory
    mem = psutil.virtual_memory()

    # Disk
    # On macOS, "/" reports APFS container size; use home dir for user-accessible space
    if platform.system() == "Darwin":
        disk = psutil.disk_usage(str(Path.home()))
    else:
        disk = psutil.disk_usage("/")

    return {
        "hostname": hostname,
        "uptime": uptime_str,
        "cpu_percent": round(cpu_percent, 1),
        "memory": {
            "total_gb": round(mem.total / (1024**3), 1),
            "used_gb": round(mem.used / (1024**3), 1),
            "percent": mem.percent,
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 1),
            "used_gb": round(disk.used / (1024**3), 1),
            "percent": round(disk.percent, 1),
        },
    }


@app.get("/api/status/claude")
async def api_claude_status():
    stats_path = Path.home() / ".claude" / "stats-cache.json"
    if not stats_path.exists():
        return {"available": False}
    try:
        data = json.loads(stats_path.read_text())
        return {
            "available": True,
            "total_messages": data.get("totalMessages", 0),
            "total_sessions": data.get("totalSessions", 0),
            "daily_activity": data.get("dailyActivity", [])[-7:],
            "model_usage": data.get("modelUsage", {}),
            "last_computed": data.get("lastComputedDate", ""),
        }
    except Exception:
        return {"available": False}


@app.get("/api/status/tailscale")
async def api_tailscale_status():
    try:
        proc = await asyncio.create_subprocess_exec(
            "tailscale", "status", "--json",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        except asyncio.TimeoutError:
            return {"available": False}
        if proc.returncode != 0:
            return {"available": False}
        data = json.loads(stdout.decode())
        peers = []
        for peer_id, peer in data.get("Peer", {}).items():
            peers.append({
                "hostname": peer.get("HostName", ""),
                "os": peer.get("OS", ""),
                "online": peer.get("Online", False),
                "ip": peer.get("TailscaleIPs", [""])[0] if peer.get("TailscaleIPs") else "",
            })
        self_node = data.get("Self", {})
        return {
            "available": True,
            "self": {
                "hostname": self_node.get("HostName", ""),
                "ip": self_node.get("TailscaleIPs", [""])[0] if self_node.get("TailscaleIPs") else "",
                "online": True,
            },
            "peers": peers,
        }
    except Exception:
        return {"available": False}


# --- Water ---


@app.get("/api/water/today")
async def api_water_today():
    today = date.today().isoformat()
    glasses = await get_water_today(today)
    return {"glasses": glasses}

@app.post("/api/water/increment")
async def api_water_increment():
    today = date.today().isoformat()
    glasses = await increment_water(today)
    return {"glasses": glasses}

@app.post("/api/water/decrement")
async def api_water_decrement():
    today = date.today().isoformat()
    glasses = await decrement_water(today)
    return {"glasses": glasses}

@app.post("/api/water/set")
async def api_water_set(body: WaterSetBody):
    today = date.today().isoformat()
    glasses = await set_water(today, body.glasses)
    return {"glasses": glasses}

@app.get("/api/water/week")
async def api_water_week():
    data = await get_water_week()
    return data


# --- Gratitude ---


@app.get("/api/gratitude")
async def api_gratitudes():
    items = await get_gratitudes()
    return {"items": items}

@app.post("/api/gratitude")
async def api_save_gratitude(body: GratitudeBody):
    item = await save_gratitude(body.text)
    return {"item": item}

@app.get("/api/gratitude/random")
async def api_random_gratitude():
    item = await get_random_gratitude()
    return {"item": item}


# --- Search ---


@app.get("/api/search")
async def api_search(q: str = ""):
    if not q.strip():
        return {"results": {"journal": [], "captures": [], "queue": [], "rss": []}}
    results = await search_all(q.strip())
    return {"results": results}


# --- Dashboard Age ---


@app.get("/api/status/age")
async def api_dashboard_age():
    first_launch = await get_setting("first_launch_date")
    if not first_launch:
        today = date.today().isoformat()
        await save_setting("first_launch_date", today)
        first_launch = today
    days = (date.today() - date.fromisoformat(first_launch)).days
    return {"days": days, "since": first_launch}


# --- ISS Tracker ---


@app.get("/api/status/iss")
async def api_iss_status():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://api.open-notify.org/iss-now.json", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    return {"available": False}
                data = await resp.json()
                pos = data.get("iss_position", {})
                return {
                    "available": True,
                    "latitude": float(pos.get("latitude", 0)),
                    "longitude": float(pos.get("longitude", 0)),
                    "timestamp": data.get("timestamp", 0),
                }
    except Exception as e:
        print(f"[ISS] Error: {e}")
        return {"available": False}


# --- Achievements ---


@app.get("/api/achievements")
async def api_achievements():
    today = date.today().isoformat()
    newly_awarded = await check_achievements(today)
    all_achievements = await get_achievements()
    return {"achievements": all_achievements, "new": newly_awarded}


# Serve frontend static files (production)
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
