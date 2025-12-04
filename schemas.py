# schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date

# 对应前端的 Tag 接口
class Tag(BaseModel):
    id: int
    name: str
    color: str

# 对应前端的 CreateTaskParams 接口（创建任务的请求参数）
class TaskCreate(BaseModel):
    title: str
    content: str
    status: Optional[str] = Field(default="todo", pattern="^(todo|done)$")
    priority: str = Field(pattern="^(high|medium|low|none)$")
    deadline: Optional[date] = None
    tags: Optional[List[int]] = None

# 对应前端的 UpdateTaskParams 类型
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(todo|done)$")
    priority: Optional[str] = Field(default=None, pattern="^(high|medium|low|none)$")
    deadline: Optional[date] = None
    tags: Optional[List[int]] = None
    isPinned: Optional[bool] = None

# 对应前端的 Item 接口
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