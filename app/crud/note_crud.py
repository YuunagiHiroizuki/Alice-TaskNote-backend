from sqlalchemy.orm import Session, aliased, joinedload 
from .. import models, schemas
from datetime import datetime
from fastapi import HTTPException
from typing import Optional, List
from sqlalchemy import func,or_, desc, asc


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
    
    # 预加载标签关联
    query = query.options(joinedload(models.Note.tags).joinedload(models.NoteTag.tag))
    notes = query.offset(skip).limit(limit).all()
    
    # 格式化返回数据
    note_list = []
    for note in notes:
        note_dict = {
            "id": note.id,
            "type": note.type,
            "title": note.title,
            "content": note.content,
            "priority": note.priority.value if note.priority else "none",
            "status": note.status.value if note.status else "done",
            "isPinned": note.isPinned,
            "created_at": note.created_at,
            "updated_at": note.updated_at,
            "tags": [{"id": nt.tag.id, "name": nt.tag.name, "color": nt.tag.color} for nt in note.tags]
        }
        note_list.append(note_dict)
    
    return note_list

def get_note(db: Session, note_id: int):
    note = db.query(models.Note).options(
        joinedload(models.Note.tags).joinedload(models.NoteTag.tag)
    ).filter(models.Note.id == note_id).first()
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


# 笔记
def create_note(db: Session, note: schemas.NoteCreate):
    db_note = models.Note(title=note.title, content=note.content)
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
    update_data = note_update.model_dump(exclude_unset=True)  
    if "tags" in update_data:
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
    for key, value in update_data.items():
        if key != "tags":  # 标签已单独处理
            setattr(db_note, key, value)
    
    db_note.updated_at = datetime.now()
    db.commit()
    db.refresh(db_note)
    
    return get_note(db, db_note.id)

# 删除笔记
def delete_note(db: Session, note_id: int):
    db_note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not db_note:
        return False
    
    # 先删除所有相关的中间表记录
    db.query(models.NoteTag).filter(models.NoteTag.note_id == note_id).delete()
    
    # 然后删除笔记本身
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
    
    # 预加载标签关联
    query = query.options(joinedload(models.Note.tags).joinedload(models.NoteTag.tag))
    # 置顶优先，按更新时间倒序
    notes = query.order_by(desc(models.Note.isPinned), desc(models.Note.updated_at)).all()
    
    note_list = []
    for note in notes:
        note_dict = {
            "id": note.id,
            "type": note.type,
            "title": note.title,
            "content": note.content,
            "priority": note.priority.value if note.priority else "none", 
            "status": note.status.value if note.status else "done",
            "isPinned": note.isPinned,
            "created_at": note.created_at,
            "updated_at": note.updated_at,
            "tags": [{"id": nt.tag.id, "name": nt.tag.name, "color": nt.tag.color} for nt in note.tags]
        }
        note_list.append(note_dict)
    
    return note_list