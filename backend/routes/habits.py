import asyncio
from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel, Field

from db import (
    FOCUS_GOAL_MINUTES,
    get_pomodoro_total,
    get_habit_completions,
    get_sleep_log,
    get_workout,
    get_mood,
    get_custom_habits,
    toggle_habit,
    add_custom_habit,
    delete_custom_habit,
)

router = APIRouter()


class CustomHabitBody(BaseModel):
    name: str = Field(min_length=1, max_length=100)


@router.get("/api/habits/today")
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
        "focus_achieved": total_minutes >= FOCUS_GOAL_MINUTES,
        "workout": workout.get("completed", 0) if workout else 0,
        "night_routine": "night_routine" in completions,
        "sleep_tracked": sleep is not None,
        "mood_logged": mood is not None,
        "custom_habits": {},
    }
    for ch in custom_habits_list:
        result["custom_habits"][ch["name"]] = ch["name"] in completions
    return result


@router.post("/api/habits/toggle/{habit}")
async def api_toggle_habit(habit: str):
    today = date.today().isoformat()
    done = await toggle_habit(today, habit)
    return {"done": done}


# --- Custom Habits ---


@router.get("/api/habits/custom")
async def api_custom_habits():
    habits = await get_custom_habits()
    return {"habits": habits}


@router.post("/api/habits/custom")
async def api_add_custom_habit(body: CustomHabitBody):
    habit = await add_custom_habit(body.name)
    return {"habit": habit}


@router.delete("/api/habits/custom/{habit_id}")
async def api_delete_custom_habit(habit_id: int):
    await delete_custom_habit(habit_id)
    return {"ok": True}
