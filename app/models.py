<<<<<<< HEAD
<<<<<<< HEAD
from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base
=======
# models.py - 在现有基础上添加统计相关模型
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, DateTime, Text, JSON, Enum, Float, DateTime
from sqlalchemy.orm import relationship
>>>>>>> feature/stats
=======
# models.py - 更新 Note 模型
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, DateTime, Text, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base
>>>>>>> feature/note-v2
from datetime import datetime
import enum
from .database import Base

# 优先级枚举
class PriorityEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# 状态枚举
class StatusEnum(str, enum.Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"

# ========== 原有模型保持不变 ==========
class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    color = Column(String)
    # 关联任务和笔记（多对多）
    tasks = relationship("TaskTag", back_populates="tag")
    notes = relationship("NoteTag", back_populates="tag")

class TaskTag(Base):
    __tablename__ = "task_tags"

    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)
    task = relationship("Task", back_populates="tags")
    tag = relationship("Tag", back_populates="tasks")

class NoteTag(Base):
    __tablename__ = "note_tags"

    note_id = Column(Integer, ForeignKey("notes.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)
    note = relationship("Note", back_populates="tags")
    tag = relationship("Tag", back_populates="notes")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, default="task")
    title = Column(String, index=True)
    content = Column(String)
    status = Column(String, default="todo")
    priority = Column(String, default="none")
    deadline = Column(Date, nullable=True)
    isPinned = Column(Boolean, default=False)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = relationship("TaskTag", back_populates="task")

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, default="note")  # 固定为 note
    title = Column(String, default="未命名笔记")
    content = Column(Text, default="")
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.MEDIUM)
    status = Column(Enum(StatusEnum), default=StatusEnum.DONE)
    isPinned = Column(Boolean, default=False)
    tags = relationship("NoteTag", back_populates="note")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ========== 新增统计相关模型 ==========
class DailyStat(Base):
    """每日统计"""
    __tablename__ = "daily_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True, unique=True)  # 格式: YYYY-MM-DD
    
    # 今日统计
    completed = Column(Integer, default=0)
    in_progress = Column(Integer, default=0)
    remaining = Column(Integer, default=0)
    total = Column(Integer, default=0)
    
    # 优先级统计（存储为JSON）
    priority_stats = Column(JSON, default={
        "high": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0},
        "medium": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0},
        "low": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0}
    })
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WeeklyStat(Base):
    """每周统计"""
    __tablename__ = "weekly_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    week_start = Column(String, index=True)  # 周开始日期: YYYY-MM-DD
    week_data = Column(JSON, default=[])  # 一周的每日数据
    created_at = Column(DateTime, default=datetime.utcnow)

class MonthlyStat(Base):
    """每月统计"""
    __tablename__ = "monthly_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    month = Column(String, index=True)  # 格式: YYYY-MM
    month_data = Column(JSON, default=[])  # 30天的数据
    created_at = Column(DateTime, default=datetime.utcnow)

class YearlyStat(Base):
    """年度统计"""
    __tablename__ = "yearly_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    year = Column(String, index=True)  # 格式: YYYY
    year_data = Column(JSON, default=[])  # 12个月的数据
    created_at = Column(DateTime, default=datetime.utcnow)