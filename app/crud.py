
# ========== Task 相关函数（保持不变）==========
from sqlalchemy.orm import Session, aliased
from . import models, schemas
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

def get_task(db: Session, task_id: int):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return None
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

def create_task(db: Session, task: schemas.TaskCreate):
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

    if task.tags:
        tags = db.query(models.Tag).filter(models.Tag.id.in_(task.tags)).all()
        if len(tags) != len(task.tags):
            raise HTTPException(status_code=400, detail="Invalid tag ID(s)")
        for tag in tags:
            task_tag = models.TaskTag(task_id=db_task.id, tag_id=tag.id)
            db.add(task_tag)
        db.commit()

    return get_task(db, db_task.id)

def update_task(db: Session, task_id: int, task: schemas.TaskUpdate):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        return None
    
    update_data = task.model_dump(exclude_unset=True)

    if "tags" in update_data:

        db.query(models.TaskTag).filter(models.TaskTag.task_id == task_id).delete()
        
        tag_ids = update_data["tags"]
        if tag_ids:
            # 批量查询标签是否存在
            tags = db.query(models.Tag).filter(models.Tag.id.in_(tag_ids)).all()
            if len(tags) != len(tag_ids):

                 pass 
            
            for tag in tags:
                task_tag = models.TaskTag(task_id=task_id, tag_id=tag.id)
                db.add(task_tag)

    #  处理常规字段
    for key, value in update_data.items():
        if key == "tags": 
            continue
            
        if hasattr(db_task, key):
            setattr(db_task, key, value)

    db_task.updatedAt = datetime.now()
    
    try:
        db.commit()
        db.refresh(db_task)
    except Exception as e:
        db.rollback()
        raise e
        
    return get_task(db, db_task.id)

def delete_task(db: Session, task_id: int):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        return False
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

# ========== Note 相关函数 ==========

def get_notes(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    tag_ids: Optional[List[int]] = None,
    pinned: Optional[bool] = None,
    sort_by: str = "updated_at",
    order: str = "desc"
):
    query = db.query(models.Note)
    
    # 搜索条件
    if search:
        query = query.filter(
            or_(
                models.Note.title.ilike(f"%{search}%"),
                models.Note.content.ilike(f"%{search}%")
            )
        )
    
    # 标签筛选
    if tag_ids:
        # 使用子查询找到包含指定标签的笔记
        for tag_id in tag_ids:
            subquery = db.query(models.NoteTag.note_id).filter(
                models.NoteTag.tag_id == tag_id
            ).subquery()
            query = query.filter(models.Note.id.in_(subquery))
    
    # 置顶筛选
    if pinned is not None:
        query = query.filter(models.Note.isPinned == pinned)
    
    # 排序
    order_func = desc if order == "desc" else asc
    
    if sort_by == "title":
        query = query.order_by(order_func(models.Note.title))
    elif sort_by == "created_at":
        query = query.order_by(order_func(models.Note.created_at))
    elif sort_by == "isPinned":
        # 置顶优先，然后按更新时间排序
        query = query.order_by(desc(models.Note.isPinned), order_func(models.Note.updated_at))
    else:
        # 默认：置顶优先，按更新时间倒序
        query = query.order_by(desc(models.Note.isPinned), desc(models.Note.updated_at))
    
    notes = query.offset(skip).limit(limit).all()
    
    # 格式化返回数据
    note_list = []
    for note in notes:
        note_dict = {
            "id": note.id,
            "type": note.type,
            "title": note.title,
            "content": note.content,
            "priority": note.priority.value if note.priority else "medium",
            "status": note.status.value if note.status else "done",
            "isPinned": note.isPinned,
            "created_at": note.created_at,
            "updated_at": note.updated_at,
            "tags": [{"id": nt.tag.id, "name": nt.tag.name, "color": nt.tag.color} for nt in note.tags]
        }
        note_list.append(note_dict)
    
    return note_list

def get_note(db: Session, note_id: int):
    note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not note:
        return None
    
    return {
        "id": note.id,
        "type": note.type,
        "title": note.title,
        "content": note.content,
        "priority": note.priority.value if note.priority else "medium",
        "status": note.status.value if note.status else "done",
        "isPinned": note.isPinned,
        "created_at": note.created_at,
        "updated_at": note.updated_at,
        "tags": [{"id": nt.tag.id, "name": nt.tag.name, "color": nt.tag.color} for nt in note.tags]
    }

def create_note(db: Session, note: schemas.NoteCreate):
    db_note = models.Note(
        title=note.title,
        content=note.content,
        priority=note.priority,
        status=note.status,
        isPinned=note.isPinned if note.isPinned else False
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    # 处理标签关联
    if note.tags:
        tags = db.query(models.Tag).filter(models.Tag.id.in_(note.tags)).all()
        if len(tags) != len(note.tags):
            raise HTTPException(status_code=400, detail="Invalid tag ID(s)")
        for tag in tags:
            note_tag = models.NoteTag(note_id=db_note.id, tag_id=tag.id)
            db.add(note_tag)
        db.commit()

    return get_note(db, db_note.id)

def update_note(db: Session, note_id: int, note_update: schemas.NoteUpdate):
    db_note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not db_note:
        return None
    
    # 更新标签关联
    if "tags" in note_update.dict(exclude_unset=True):
        # 删除现有标签关联
        db.query(models.NoteTag).filter(models.NoteTag.note_id == note_id).delete()
        # 添加新的标签关联
        if note_update.tags:
            tags = db.query(models.Tag).filter(models.Tag.id.in_(note_update.tags)).all()
            if len(tags) != len(note_update.tags):
                raise HTTPException(status_code=400, detail="Invalid tag ID(s)")
            for tag in tags:
                note_tag = models.NoteTag(note_id=note_id, tag_id=tag.id)
                db.add(note_tag)
    
    # 更新其他字段
    update_data = note_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key != "tags":  # 标签已单独处理
            setattr(db_note, key, value)
    
    db_note.updated_at = datetime.now()
    db.commit()
    db.refresh(db_note)
    
    return get_note(db, db_note.id)

def delete_note(db: Session, note_id: int):
    db_note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not db_note:
        return False
    db.delete(db_note)
    db.commit()
    return True

def toggle_pin_note(db: Session, note_id: int):
    db_note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not db_note:
        return None
    
    db_note.isPinned = not db_note.isPinned
    db_note.updated_at = datetime.now()
    db.commit()
    db.refresh(db_note)
    
    return get_note(db, db_note.id)

def search_notes(db: Session, keyword: Optional[str] = None, tag: Optional[int] = None):
    query = db.query(models.Note)
    
    if keyword:
        query = query.filter(
            or_(
                models.Note.title.ilike(f"%{keyword}%"),
                models.Note.content.ilike(f"%{keyword}%")
            )
        )
    
    if tag:
        # 通过中间表找到包含指定标签的笔记
        subquery = db.query(models.NoteTag.note_id).filter(
            models.NoteTag.tag_id == tag
        ).subquery()
        query = query.filter(models.Note.id.in_(subquery))
    
    # 置顶优先，按更新时间倒序
    notes = query.order_by(desc(models.Note.isPinned), desc(models.Note.updated_at)).all()
    
    note_list = []
    for note in notes:
        note_dict = {
            "id": note.id,
            "type": note.type,
            "title": note.title,
            "content": note.content,
            "priority": note.priority.value if note.priority else "medium",
            "status": note.status.value if note.status else "done",
            "isPinned": note.isPinned,
            "created_at": note.created_at,
            "updated_at": note.updated_at,
            "tags": [{"id": nt.tag.id, "name": nt.tag.name, "color": nt.tag.color} for nt in note.tags]
        }
        note_list.append(note_dict)
    
    return note_list

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
