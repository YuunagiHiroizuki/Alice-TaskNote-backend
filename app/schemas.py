# schemas.py - 添加 Note 相关的模型
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class PriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class StatusEnum(str, Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"

# Tag 模型保持不变
class Tag(BaseModel):
    id: int
    name: str
    color: str

    class Config:
        orm_mode = True

# Note 创建模型
class NoteCreate(BaseModel):
    title: Optional[str] = "未命名笔记"
    content: Optional[str] = ""
    priority: Optional[PriorityEnum] = PriorityEnum.MEDIUM
    status: Optional[StatusEnum] = StatusEnum.DONE
    tags: Optional[List[int]] = None
    isPinned: Optional[bool] = False

# Note 更新模型
class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    status: Optional[StatusEnum] = None
    tags: Optional[List[int]] = None
    isPinned: Optional[bool] = None

# Note 响应模型
class NoteResponse(BaseModel):
    id: int
    type: str = "note"
    title: str
    content: str
    priority: str
    status: str
    isPinned: bool
    tags: Optional[List[Tag]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# 搜索参数模型
class NoteSearchParams(BaseModel):
    search: Optional[str] = None
    tags: Optional[List[int]] = None
    pinned: Optional[bool] = None
    sort_by: Optional[str] = "updated_at"
    order: Optional[str] = "desc"

# Task 模型保持不变
class TaskCreate(BaseModel):
    title: str
    content: str
    status: Optional[str] = Field(default="todo", pattern="^(todo|done)$")
    priority: str = Field(pattern="^(high|medium|low|none)$")
    deadline: Optional[date] = None
    tags: Optional[List[int]] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(todo|done)$")
    priority: Optional[str] = Field(default=None, pattern="^(high|medium|low|none)$")
    deadline: Optional[date] = None
    tags: Optional[List[int]] = None
    isPinned: Optional[bool] = None

class TaskResponse(BaseModel):
    id: int
    type: str = "task"
    title: str
    content: str
    status: str = Field(pattern="^(todo|done)$")
    priority: str = Field(pattern="^(high|medium|low|none)$")
    deadline: Optional[date] = None
    tags: Optional[List[Tag]] = None
    isPinned: bool
    createdAt: str
    updatedAt: str

    class Config:
        orm_mode = True