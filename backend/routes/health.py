from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel, Field

from db import (
    get_sleep_log,
    save_sleep_log,
    get_sleep_week,
    get_workout,
    toggle_workout,
    save_workout_note,
    get_mood,
    save_mood,
    get_water_today,
    increment_water,
    decrement_water,
    set_water,
    get_water_week,
)

router = APIRouter()


class SleepBody(BaseModel):
    bedtime: str
    wake_time: str


class WorkoutNoteBody(BaseModel):
    note: str = Field(max_length=2000)


class MoodBody(BaseModel):
    mood: int = Field(ge=1, le=5)


class WaterSetBody(BaseModel):
    glasses: int


# --- Sleep ---


@router.get("/api/sleep/week")
async def api_sleep_week():
    today = date.today().isoformat()
    days = await get_sleep_week(today)
    return {"days": days}


@router.get("/api/sleep/today")
async def api_sleep_today():
    today = date.today().isoformat()
    sleep = await get_sleep_log(today)
    return {"sleep": sleep}


@router.put("/api/sleep/today")
async def api_save_sleep_today(body: SleepBody):
    today = date.today().isoformat()
    sleep = await save_sleep_log(today, body.bedtime, body.wake_time)
    return {"sleep": sleep}


# --- Workout ---


@router.get("/api/workout/today")
async def api_workout_today():
    today = date.today().isoformat()
    workout = await get_workout(today)
    return {"workout": workout}


@router.post("/api/workout/today/toggle")
async def api_toggle_workout_today():
    today = date.today().isoformat()
    completed = await toggle_workout(today)
    return {"completed": completed}


@router.put("/api/workout/today")
async def api_save_workout_today(body: WorkoutNoteBody):
    today = date.today().isoformat()
    workout = await save_workout_note(today, body.note)
    return {"workout": workout}


# --- Mood ---


@router.get("/api/mood/today")
async def api_mood_today():
    today = date.today().isoformat()
    mood = await get_mood(today)
    return {"mood": mood}


@router.put("/api/mood/today")
async def api_save_mood_today(body: MoodBody):
    today = date.today().isoformat()
    mood = await save_mood(today, body.mood)
    return {"mood": mood}


# --- Water ---


@router.get("/api/water/today")
async def api_water_today():
    today = date.today().isoformat()
    glasses = await get_water_today(today)
    return {"glasses": glasses}


@router.post("/api/water/increment")
async def api_water_increment():
    today = date.today().isoformat()
    glasses = await increment_water(today)
    return {"glasses": glasses}


@router.post("/api/water/decrement")
async def api_water_decrement():
    today = date.today().isoformat()
    glasses = await decrement_water(today)
    return {"glasses": glasses}


@router.post("/api/water/set")
async def api_water_set(body: WaterSetBody):
    today = date.today().isoformat()
    glasses = await set_water(today, body.glasses)
    return {"glasses": glasses}


@router.get("/api/water/week")
async def api_water_week():
    data = await get_water_week()
    return data
