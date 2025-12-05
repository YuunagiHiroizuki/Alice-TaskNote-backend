from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime
from fastapi import HTTPException
from typing import Optional


def get_tasks(db: Session):
    tasks = db.query(models.Task).all()
    # 处理标签关联（前端需要完整的 Tag 信息）
    task_list = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "type": task.type,
            "title": task.title,
            "content": task.content,
            "status": task.status,
            "priority": task.priority,
            "deadline": task.deadline,
            "isPinned": task.isPinned,
            "createdAt": task.createdAt.strftime("%Y-%m-%d %H:%M:%S"),
            "updatedAt": task.updatedAt.strftime("%Y-%m-%d %H:%M:%S"),
            "tags": [{"id": tt.tag.id, "name": tt.tag.name, "color": tt.tag.color} for tt in task.tags]
        }
        task_list.append(task_dict)
    return task_list

# 2. 获取单个任务
def get_task(db: Session, task_id: int):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return None
    # 组装标签信息
    task_dict = {
        "id": task.id,
        "type": task.type,
        "title": task.title,
        "content": task.content,
        "status": task.status,
        "priority": task.priority,
        "deadline": task.deadline,
        "isPinned": task.isPinned,
        "createdAt": task.createdAt.strftime("%Y-%m-%d %H:%M:%S"),
        "updatedAt": task.updatedAt.strftime("%Y-%m-%d %H:%M:%S"),
        "tags": [{"id": tt.tag.id, "name": tt.tag.name, "color": tt.tag.color} for tt in task.tags]
    }
    return task_dict

# 3. 创建任务
def create_task(db: Session, task: schemas.TaskCreate):
    # 创建任务实例
    db_task = models.Task(
        title=task.title,
        content=task.content,
        status=task.status,
        priority=task.priority,
        deadline=task.deadline,
        isPinned=False  # 默认不置顶
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    if task.tags:
        # 批量查询标签是否存在
        tags = db.query(models.Tag).filter(models.Tag.id.in_(task.tags)).all()
        if len(tags) != len(task.tags):
            # 存在无效标签ID
            raise HTTPException(status_code=400, detail="Invalid tag ID(s)")
        # 建立关联
        for tag in tags:
            task_tag = models.TaskTag(task_id=db_task.id, tag_id=tag.id)
            db.add(task_tag)
        db.commit()

    return get_task(db, db_task.id)

# 4. 更新任务
def update_task(db: Session, task_id: int, task: schemas.TaskUpdate):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        return None
    
    if "tags" in task.dict(exclude_unset=True):
        # 先删除现有关联
        db.query(models.TaskTag).filter(models.TaskTag.task_id == task_id).delete()
        # 新增关联（同创建逻辑）
        if task.tags:
            tags = db.query(models.Tag).filter(models.Tag.id.in_(task.tags)).all()
            if len(tags) != len(task.tags):
                raise HTTPException(status_code=400, detail="Invalid tag ID(s)")
            for tag in tags:
                task_tag = models.TaskTag(task_id=task_id, tag_id=tag.id)
                db.add(task_tag)

    update_data = task.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key != "tags":  # 标签单独处理，先忽略
            setattr(db_task, key, value)
    db_task.updatedAt = datetime.now()
    db.commit()
    db.refresh(db_task)
    return get_task(db, db_task.id)

# 5. 删除任务
def delete_task(db: Session, task_id: int):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        return False
    db.delete(db_task)
    db.commit()
    return True

# 6. 搜索任务
def search_tasks(db: Session, query: str):
    tasks = db.query(models.Task).filter(
        (models.Task.title.ilike(f"%{query}%")) | 
        (models.Task.content.ilike(f"%{query}%"))
    ).all()
    task_list = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "type": task.type,
            "title": task.title,
            "content": task.content,
            "status": task.status,
            "priority": task.priority,
            "deadline": task.deadline,
            "isPinned": task.isPinned,
            "createdAt": task.createdAt.strftime("%Y-%m-%d %H:%M:%S"),
            "updatedAt": task.updatedAt.strftime("%Y-%m-%d %H:%M:%S"),
            "tags": [{"id": tt.tag.id, "name": tt.tag.name, "color": tt.tag.color} for tt in task.tags]
        }
        task_list.append(task_dict)
    return task_list

# 笔记
def create_note(db: Session, note: schemas.NoteCreate):
    db_note = models.Note(title=note.title, content=note.content)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

def get_notes(db: Session):
    return db.query(models.Note).all()
