import asyncio
import base64
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pywebpush import webpush, WebPushException

from db import (
    init_db,
    get_latest_hn_posts,
    get_latest_youtube_videos,
    get_journal_dates,
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
    get_sleep_log,
    save_sleep_log,
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
)
from hn import fetch_top_hn_posts
from youtube import fetch_youtube_recommendations
from weather import geocode_zip, fetch_weather

import json

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
    payload = json.dumps({"title": title, "body": body})
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub["endpoint"],
                    "keys": {"p256dh": sub["p256dh"], "auth": sub["auth"]},
                },
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": "mailto:noreply@base.local"},
            )
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


class SleepBody(BaseModel):
    bedtime: str
    wake_time: str


class WorkoutNoteBody(BaseModel):
    note: str


class MoodBody(BaseModel):
    mood: int


class CaptureBody(BaseModel):
    text: str


class CustomHabitBody(BaseModel):
    name: str

FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "build"

scheduler = AsyncIOScheduler()


async def scheduled_fetch(notify: bool = True):
    print("[Scheduler] Running scheduled fetch...")
    results = await asyncio.gather(
        fetch_top_hn_posts(),
        fetch_youtube_recommendations(),
        return_exceptions=True,
    )
    for name, result in zip(["HN", "YouTube"], results):
        if isinstance(result, Exception):
            print(f"[Scheduler] {name} fetch failed: {result}")
    if notify:
        await send_push_to_all("Base", "New content ready")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("[Base] Database initialized")
    await load_or_create_vapid_keys()

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
    videos = await get_latest_youtube_videos()
    return {"videos": videos}


@app.post("/api/refresh/hn")
async def refresh_hn():
    posts = await fetch_top_hn_posts()
    return {"posts": posts, "refreshed": True}


@app.post("/api/refresh/youtube")
async def refresh_youtube():
    videos = await fetch_youtube_recommendations()
    return {"videos": videos, "refreshed": True}


@app.get("/api/journal/dates")
async def api_journal_dates():
    dates = await get_journal_dates()
    return {"dates": dates}


@app.get("/api/journal/today")
async def api_journal_today():
    today = date.today().isoformat()
    entry = await get_journal_entry(today)
    return {"entry": entry}


@app.get("/api/journal/{entry_date}")
async def api_journal_by_date(entry_date: str):
    entry = await get_journal_entry(entry_date)
    return {"entry": entry}


@app.put("/api/journal/today")
async def api_save_journal_today(body: JournalBody):
    today = date.today().isoformat()
    entry = await save_journal_entry(today, body.content)
    return {"entry": entry}


@app.put("/api/journal/{entry_date}")
async def api_save_journal(entry_date: str, body: JournalBody):
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
        return {"error": "Could not find location", "zip_code": body.zip_code}
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


# --- Sleep ---


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


@app.get("/api/review/week")
async def api_review_week():
    today = date.today().isoformat()
    return await get_weekly_review(today)


# Serve frontend static files (production)
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
