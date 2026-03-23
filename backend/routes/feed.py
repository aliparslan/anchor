from fastapi import APIRouter
from pydantic import BaseModel, Field

from db import (
    get_latest_hn_posts,
    get_latest_youtube_videos,
    get_rss_items,
    get_dismissed_rss_ids,
    dismiss_rss_item,
    get_dismissed_video_ids,
    dismiss_video,
    get_reading_queue,
    save_to_reading_queue,
    mark_queue_item_read,
    delete_queue_item,
    delete_queue_item_by_hn_id,
    mark_queue_item_unread,
)
from hn import fetch_top_hn_posts
from youtube import fetch_youtube_recommendations
from rss import fetch_all_feeds

router = APIRouter()


class ReadingQueueBody(BaseModel):
    hn_id: int | None = None
    title: str = Field(max_length=500)
    url: str = Field(max_length=2000)
    domain: str | None = None


@router.get("/api/hn")
async def api_hn():
    posts = await get_latest_hn_posts()
    return {"posts": posts}


@router.get("/api/youtube")
async def api_youtube():
    videos = await get_latest_youtube_videos(limit=30)
    return {"videos": videos}


@router.post("/api/refresh/hn")
async def refresh_hn():
    posts = await fetch_top_hn_posts()
    return {"posts": posts, "refreshed": True}


@router.post("/api/refresh/youtube")
async def refresh_youtube():
    videos = await fetch_youtube_recommendations(count=30)
    return {"videos": videos, "refreshed": True}


@router.get("/api/rss")
async def api_rss():
    items = await get_rss_items(limit=50)
    dismissed = set(await get_dismissed_rss_ids())
    items = [i for i in items if i["id"] not in dismissed]
    return {"items": items}


@router.post("/api/refresh/rss")
async def api_refresh_rss():
    await fetch_all_feeds()
    items = await get_rss_items(limit=50)
    dismissed = set(await get_dismissed_rss_ids())
    items = [i for i in items if i["id"] not in dismissed]
    return {"items": items, "refreshed": True}


@router.get("/api/rss/dismissed")
async def api_dismissed_rss():
    ids = await get_dismissed_rss_ids()
    return {"dismissed": ids}


@router.post("/api/rss/dismiss/{item_id}")
async def api_dismiss_rss(item_id: int):
    await dismiss_rss_item(item_id)
    return {"ok": True}


@router.get("/api/videos/dismissed")
async def api_dismissed_videos():
    ids = await get_dismissed_video_ids()
    return {"dismissed": ids}


@router.post("/api/videos/dismiss/{video_id}")
async def api_dismiss_video(video_id: str):
    await dismiss_video(video_id)
    return {"ok": True}


@router.get("/api/reading-queue")
async def api_reading_queue():
    items = await get_reading_queue()
    return {"items": items}


@router.post("/api/reading-queue")
async def api_save_reading_queue(body: ReadingQueueBody):
    item = await save_to_reading_queue(body.hn_id, body.title, body.url, body.domain)
    return {"item": item}


@router.post("/api/reading-queue/{item_id}/read")
async def api_mark_queue_read(item_id: int):
    await mark_queue_item_read(item_id)
    return {"ok": True}


@router.delete("/api/reading-queue/{item_id}")
async def api_delete_queue_item(item_id: int):
    await delete_queue_item(item_id)
    return {"ok": True}


@router.delete("/api/reading-queue/by-hn/{hn_id}")
async def api_delete_queue_by_hn(hn_id: int):
    await delete_queue_item_by_hn_id(hn_id)
    return {"ok": True}


@router.post("/api/reading-queue/{item_id}/unread")
async def api_mark_queue_unread(item_id: int):
    await mark_queue_item_unread(item_id)
    return {"ok": True}
