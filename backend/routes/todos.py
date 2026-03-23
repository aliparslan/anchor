from fastapi import APIRouter
from pydantic import BaseModel, Field

from db import (
    get_todos,
    create_todo,
    update_todo,
    complete_todo,
    undo_todo,
    delete_todo,
    reorder_todos,
)

router = APIRouter()


class TodoBody(BaseModel):
    text: str = Field(max_length=2000)


class TodoReorderBody(BaseModel):
    ids: list[int]


@router.get("/api/todos")
async def api_todos():
    todos = await get_todos()
    return {"todos": todos}


@router.post("/api/todos")
async def api_create_todo(body: TodoBody):
    todo = await create_todo(body.text)
    return {"todo": todo}


@router.put("/api/todos/{todo_id}")
async def api_update_todo(todo_id: int, body: TodoBody):
    todo = await update_todo(todo_id, body.text)
    return {"todo": todo}


@router.post("/api/todos/{todo_id}/complete")
async def api_complete_todo(todo_id: int):
    todo = await complete_todo(todo_id)
    return {"todo": todo}


@router.post("/api/todos/{todo_id}/undo")
async def api_undo_todo(todo_id: int):
    todo = await undo_todo(todo_id)
    return {"todo": todo}


@router.delete("/api/todos/{todo_id}")
async def api_delete_todo(todo_id: int):
    await delete_todo(todo_id)
    return {"ok": True}


@router.post("/api/todos/reorder")
async def api_reorder_todos(body: TodoReorderBody):
    await reorder_todos(body.ids)
    return {"ok": True}
