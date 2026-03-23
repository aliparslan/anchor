from datetime import date

from fastapi import APIRouter

from db import (
    get_daily_summary,
    get_habits_week,
    get_streaks,
    get_focus_month,
    get_streak,
    get_daily_score,
    get_weekly_review,
)

router = APIRouter()


@router.get("/api/summary/today")
async def api_summary_today():
    today = date.today().isoformat()
    return await get_daily_summary(today)


@router.get("/api/habits/week")
async def api_habits_week():
    today = date.today().isoformat()
    return await get_habits_week(today)


@router.get("/api/habits/streaks")
async def api_habits_streaks():
    today = date.today().isoformat()
    streaks = await get_streaks(today)
    return {"streaks": streaks}


@router.get("/api/focus/month")
async def api_focus_month():
    today = date.today().isoformat()
    days = await get_focus_month(today)
    return {"days": days}


@router.get("/api/streak")
async def api_streak():
    today = date.today().isoformat()
    streak = await get_streak(today)
    return {"streak": streak}


@router.get("/api/score/today")
async def api_score_today():
    today = date.today().isoformat()
    return await get_daily_score(today)


@router.get("/api/review/week")
async def api_review_week():
    today = date.today().isoformat()
    return await get_weekly_review(today)
