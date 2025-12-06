from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from datetime import date, datetime
from enum import Enum

# ========== 原有模型保持不变，只修改Config ==========
class PriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class StatusEnum(str, Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"

class Tag(BaseModel):
    id: int
    name: str
    color: str
    
    model_config = ConfigDict(from_attributes=True)  # 改为新的配置方式

class TodoCreate(BaseModel):
    title: str
    is_done: Optional[bool] = False
    
class TodoOut(TodoCreate):
    id: int
    created_at: str

    model_config = {
        "from_attributes": True
    }




class NoteCreate(BaseModel):
    title: Optional[str] = "未命名笔记"
    content: Optional[str] = ""
    priority: Optional[PriorityEnum] = PriorityEnum.MEDIUM
    status: Optional[StatusEnum] = StatusEnum.DONE
    tags: Optional[List[int]] = None
    isPinned: Optional[bool] = False

class NoteOut(NoteCreate):
    id: int
    created_at: str

    model_config = {
        "from_attributes": True
    }
class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    status: Optional[StatusEnum] = None
    tags: Optional[List[int]] = None
    isPinned: Optional[bool] = None

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
    
    model_config = ConfigDict(from_attributes=True)  # 改为新的配置方式

class NoteSearchParams(BaseModel):
    search: Optional[str] = None
    tags: Optional[List[int]] = None
    pinned: Optional[bool] = None
    sort_by: Optional[str] = "updated_at"
    order: Optional[str] = "desc"

class NoteOut(NoteCreate):
    id: int
    created_at: str

    model_config = {
        "from_attributes": True
    }
    
class TaskCreate(BaseModel):
    title: str
    content: str
    status: Optional[str] = Field(default="todo", pattern="^(todo|doing|done)$")
    priority: str = Field(pattern="^(high|medium|low|none)$")
    deadline: Optional[date] = None
    tags: Optional[List[int]] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(todo|doing|done)$")
    isPinned: Optional[bool] = None
    priority: Optional[str] = Field(default=None, pattern="^(high|medium|low|none)$")
    deadline: Optional[date] = None
    tags: Optional[List[int]] = None
    

class TaskResponse(BaseModel):
    id: int
    type: str = "task"
    title: str
    content: str
    status: str = Field(pattern="^(todo|doing|done)$")
    priority: str = Field(pattern="^(high|medium|low|none)$")
    deadline: Optional[date] = None
    tags: Optional[List[Tag]] = None
    isPinned: bool
    createdAt: str
    updatedAt: str
    
    model_config = ConfigDict(from_attributes=True)  # 改为新的配置方式

<<<<<<< HEAD
# ========== 新增统计模型 ==========
class TodayStats(BaseModel):
    completed: int
    inProgress: int
    remaining: int
    total: int
=======
    class Config:
        orm_mode = True
>>>>>>> feature/note-v2

class WeekDataPoint(BaseModel):
    day: str
    completed: int
    inProgress: int
    remaining: int

class MonthDataPoint(BaseModel):
    date: str
    completed: int
    inProgress: int
    remaining: int
    id: int
    name: str
    color: Optional[str] = None
    count: int 
    
    class Config:
        orm_mode = True 

class YearDataPoint(BaseModel):
    month: str
    completed: int
    inProgress: int
    remaining: int

class PriorityStat(BaseModel):
    level: str
    completed: int
    inProgress: int
    remaining: int
    total: int

class StatsResponse(BaseModel):
    today: TodayStats
    week: List[WeekDataPoint]
    month: List[MonthDataPoint]
    year: List[YearDataPoint]
    priority: List[PriorityStat]

class DailyStatCreate(BaseModel):
    date: str
    completed: int = 0
    in_progress: int = 0
    remaining: int = 0
    total: int = 0
    priority_stats: Optional[Dict] = None

class DailyStatResponse(BaseModel):
    id: int
<<<<<<< HEAD
    date: str
    completed: int
    in_progress: int
    remaining: int
    total: int
    priority_stats: Dict
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)  # 改为新的配置方式
=======
    created_at: str

    model_config = {
        "from_attributes": True
    }
>>>>>>> feature/note-v2
