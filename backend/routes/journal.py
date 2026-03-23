from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from db import (
    get_journal_dates,
    get_journal_entries_preview,
    get_journal_entry,
    save_journal_entry,
    append_journal_entry,
)

router = APIRouter()


class JournalBody(BaseModel):
    content: str = Field(max_length=50000)


@router.get("/api/journal/dates")
async def api_journal_dates():
    dates = await get_journal_dates()
    return {"dates": dates}


@router.get("/api/journal/entries")
async def api_journal_entries(limit: int = 20, offset: int = 0):
    entries = await get_journal_entries_preview(limit=limit, offset=offset)
    return {"entries": entries}


@router.get("/api/journal/today")
async def api_journal_today():
    today = date.today().isoformat()
    entry = await get_journal_entry(today)
    return {"entry": entry}


@router.get("/api/journal/{entry_date}")
async def api_journal_by_date(entry_date: str):
    try:
        date.fromisoformat(entry_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format")
    entry = await get_journal_entry(entry_date)
    return {"entry": entry}


@router.put("/api/journal/today")
async def api_save_journal_today(body: JournalBody):
    today = date.today().isoformat()
    entry = await save_journal_entry(today, body.content)
    return {"entry": entry}


@router.put("/api/journal/{entry_date}")
async def api_save_journal(entry_date: str, body: JournalBody):
    try:
        date.fromisoformat(entry_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format")
    entry = await save_journal_entry(entry_date, body.content)
    return {"entry": entry}


@router.post("/api/journal/today/append")
async def api_append_journal_today(body: JournalBody):
    today = date.today().isoformat()
    entry = await append_journal_entry(today, body.content)
    return {"entry": entry}
