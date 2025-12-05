# models.py - 更新 Note 模型
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, DateTime, Text, JSON, Enum
from sqlalchemy.orm import relationship
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

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    color = Column(String)
    # 关联任务和笔记（多对多）
    tasks = relationship("TaskTag", back_populates="tag")
    notes = relationship("NoteTag", back_populates="tag")

# 任务-标签中间表
class TaskTag(Base):
    __tablename__ = "task_tags"

    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)
    task = relationship("Task", back_populates="tags")
    tag = relationship("Tag", back_populates="tasks")

# 笔记-标签中间表
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