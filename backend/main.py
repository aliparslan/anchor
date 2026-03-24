import asyncio
import base64
from contextlib import asynccontextmanager
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pywebpush import webpush, WebPushException
from py_vapid import Vapid

from db import (
    init_db,
    get_setting,
    save_setting,
    get_push_subscriptions,
    delete_push_subscription,
    seed_rss_feeds,
)
from hn import fetch_top_hn_posts
from youtube import fetch_youtube_recommendations
from rss import fetch_all_feeds
from github import fetch_github_activity

from routes.feed import router as feed_router
from routes.journal import router as journal_router
from routes.health import router as health_router
from routes.habits import router as habits_router
from routes.todos import router as todos_router
from routes.settings import router as settings_router
from routes.stats import router as stats_router

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


FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "build"

scheduler = AsyncIOScheduler()


async def scheduled_fetch(notify: bool = True):
    print("[Scheduler] Running scheduled fetch...")
    results = await asyncio.gather(
        fetch_top_hn_posts(),
        fetch_youtube_recommendations(count=30),
        fetch_all_feeds(),
        fetch_github_activity(),
        return_exceptions=True,
    )
    for name, result in zip(["HN", "YouTube", "RSS", "GitHub"], results):
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

    # Expose VAPID public key and send_push_to_all via app.state for routers
    app.state.vapid_public_key = VAPID_PUBLIC_KEY
    app.state.send_push_to_all = send_push_to_all

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

app.include_router(feed_router)
app.include_router(journal_router)
app.include_router(health_router)
app.include_router(habits_router)
app.include_router(todos_router)
app.include_router(settings_router)
app.include_router(stats_router)

# Serve frontend static files (production)
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
