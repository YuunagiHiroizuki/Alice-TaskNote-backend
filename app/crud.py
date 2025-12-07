from sqlalchemy.orm import Session, aliased, joinedload 
from . import models, schemas
from datetime import datetime
from fastapi import HTTPException
from typing import Optional
from sqlalchemy import func

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
    db_task =  db.query(models.Task).filter(models.Task.id  == task_id).first()
    if db_task is None:
        return None

    # 兼容 pydantic v1/v2：优先使用 dict，若项目用 v2 可改回 model_dump
    try:
        update_data = task.dict(exclude_unset=True)
    except Exception:
        update_data = task.model_dump(exclude_unset=True)

    try:
        # 先处理 tags：先验证再修改，避免先删后查失败导致丢失
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
        # 可以记录日志 e，然后返回通用错误
        raise HTTPException(status_code=500, detail="Failed to update task")

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


# 标签
def get_tags_with_counts(db: Session):
    # 使用 func.count 和 group_by 来统计每个标签关联的任务数量
    
    # 1. 查询所有 Tag
    tags = db.query(models.Tag).all()
    
    # 2. 查询标签使用计数 (通过 TaskTag 中间表)
    tag_counts = db.query(
        models.TaskTag.tag_id, 
        func.count(models.TaskTag.task_id).label('count')
    ).group_by(models.TaskTag.tag_id).all()
    
    # 转换为字典方便查找
    count_map = {tag_id: count for tag_id, count in tag_counts}
    
    # 3. 组装最终结果
    result = []
    for tag in tags:
        result.append({
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "count": count_map.get(tag.id, 0) # 如果没有任务使用，计数为 0
        })
        
    return result

def search_tags(db: Session, query: str):
    tags = db.query(models.Tag).filter(
        models.Tag.name.ilike(f"%{query}%")
    ).all()
    
    # 依然需要附加计数信息
    tag_counts = db.query(
        models.TaskTag.tag_id, 
        func.count(models.TaskTag.task_id).label('count')
    ).group_by(models.TaskTag.tag_id).all()
    
    count_map = {tag_id: count for tag_id, count in tag_counts}
    
    result = []
    for tag in tags:
        result.append({
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "count": count_map.get(tag.id, 0)
        })
        
    return result

def create_tag(db: Session, tag: schemas.TagCreate):
    # 如果没有提供 color，给一个默认值
    tag_color = tag.color if tag.color else "#909399" 
    
    db_tag = models.Tag(name=tag.name, color=tag_color)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

def get_tag_by_name(db: Session, name: str):
    return db.query(models.Tag).filter(models.Tag.name == name).first()

def delete_tag(db: Session, tag_id: int):
    # 检查标签是否存在
    db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if not db_tag:
        return False
    
    # 先删除关联关系
    db.query(models.TaskTag).filter(models.TaskTag.tag_id == tag_id).delete()
    # 再删除标签
    db.delete(db_tag)
    db.commit()
    return True