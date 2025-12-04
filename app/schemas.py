from pydantic import BaseModel
from typing import Optional

class TodoCreate(BaseModel):
    title: str
    is_done: Optional[bool] = False

class TodoOut(TodoCreate):
    id: int
    created_at: str

    class Config:
        orm_mode = True

class NoteCreate(BaseModel):
    title: Optional[str] = "未命名笔记"
    content: Optional[str] = ""

class NoteOut(NoteCreate):
    id: int
    created_at: str

    class Config:
        orm_mode = True
