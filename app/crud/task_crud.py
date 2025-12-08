from sqlalchemy.orm import Session, aliased, joinedload 
from .. import models, schemas
from datetime import datetime
from fastapi import HTTPException
from typing import Optional, List
from sqlalchemy import func,or_, desc, asc


def get_tasks(db: Session):
    tasks = db.query(models.Task).all()
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
    task = db.query(models.Task).options(joinedload(models.Task.tags).joinedload(models.TaskTag.tag)).filter(models.Task.id == task_id).first()
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
        isPinned=False
    )
    db.add(db_task)
    db.commit() 
    db.refresh(db_task)  

    # 处理标签关联
    if task.tags:
        tags = db.query(models.Tag).filter(models.Tag.id.in_(task.tags)).all()
        if len(tags) != len(task.tags):
            raise HTTPException(status_code=400, detail="Invalid tag ID(s)")
        for tag in tags:
            task_tag = models.TaskTag(task_id=db_task.id, tag_id=tag.id)
            db.add(task_tag)
        db.commit()

    return get_task(db, db_task.id)
    
# 4. 更新任务
def update_task(db: Session, task_id: int, task: schemas.TaskUpdate):
    db_task =  db.query(models.Task).filter(models.Task.id  == task_id).first()
    if db_task is None:
        return None

    # 兼容 pydantic v1/v2：优先使用 dict，若项目用 v2 可改回 model_dump
    try:
        update_data = task.dict(exclude_unset=True)
    except Exception:
        update_data = task.model_dump(exclude_unset=True)

    try:
        if "tags" in update_data:
            tag_ids = update_data["tags"] or []
            if tag_ids:
                tags = db.query(models.Tag).filter(models.Tag.id.in_(tag_ids)).all()
                if len(tags) != len(tag_ids):
                    invalid_ids = set(tag_ids) - { t.id  for t in tags}
                    raise HTTPException(status_code=400, detail=f"Invalid tag ID(s): {list(invalid_ids)}")
            # 验证通过后，删除旧关联并新增
            db.query(models.TaskTag).filter(models.TaskTag.task_id == task_id).delete()
            for tag in db.query(models.Tag).filter(models.Tag.id.in_(tag_ids)).all():
                db.add(models.TaskTag(task_id=task_id, tag_id=tag.id))

        # 更新其他字段
        for key, value in update_data.items():
            if key == "tags":
                continue
            if hasattr(db_task, key):
                setattr(db_task, key, value)

        db_task.updatedAt = datetime.now()
        db.commit()
        db.refresh(db_task)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update task")

    return get_task(db, db_task.id)

def delete_task(db: Session, task_id: int):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        return False
    
    # 先删除所有相关的中间表记录
    db.query(models.TaskTag).filter(models.TaskTag.task_id == task_id).delete()
    
    # 然后删除任务本身
    db.delete(db_task)
    db.commit()
    return True

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




