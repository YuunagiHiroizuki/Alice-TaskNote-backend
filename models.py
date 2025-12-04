# models.py
from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# 标签表
class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    color = Column(String)
    # 关联任务（多对多，需中间表）
    tasks = relationship("TaskTag", back_populates="tag")

# 任务-标签中间表（多对多关联）
class TaskTag(Base):
    __tablename__ = "task_tags"

    task_id = Column(Integer, ForeignKey("tasks.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)
    # 关联 Task 和 Tag
    task = relationship("Task", back_populates="tags")
    tag = relationship("Tag", back_populates="tasks")

# 任务表（核心）
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, default="task")  # 固定为 task
    title = Column(String, index=True)
    content = Column(String)
    status = Column(String, default="todo")  # todo/done
    priority = Column(String, default="none")  # high/medium/low/none
    deadline = Column(Date, nullable=True)  # 截止日期
    isPinned = Column(Boolean, default=False)  # 是否置顶
    createdAt = Column(DateTime, default=datetime.now)  # 创建时间
    updatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # 更新时间
    # 关联标签（多对多）
    tags = relationship("TaskTag", back_populates="task")