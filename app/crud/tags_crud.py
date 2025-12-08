from sqlalchemy.orm import Session, aliased, joinedload 
from .. import models, schemas
from datetime import datetime
from fastapi import HTTPException
from typing import Optional, List
from sqlalchemy import func,or_, desc, asc


def get_tags_with_counts(db: Session):
    
    # 1. 查询所有 Tag
    tags = db.query(models.Tag).all()
    
    # 2. 查询标签在任务中的使用计数 (通过 TaskTag 中间表)
    task_tag_counts = db.query(
        models.TaskTag.tag_id, 
        func.count(models.TaskTag.task_id).label('count')
    ).group_by(models.TaskTag.tag_id).all()
    
    # 3. 查询标签在笔记中的使用计数 (通过 NoteTag 中间表)
    note_tag_counts = db.query(
        models.NoteTag.tag_id, 
        func.count(models.NoteTag.note_id).label('count')
    ).group_by(models.NoteTag.tag_id).all()
    
    # 转换为字典方便查找
    task_count_map = {tag_id: count for tag_id, count in task_tag_counts}
    note_count_map = {tag_id: count for tag_id, count in note_tag_counts}
    
    # 4. 组装最终结果
    result = []
    for tag in tags:
        task_count = task_count_map.get(tag.id, 0)
        note_count = note_count_map.get(tag.id, 0)
        result.append({
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "count": task_count + note_count,  # 总计数
            "task_count": task_count,
            "note_count": note_count
        })
        
    return result

def search_tags(db: Session, query: str):
    tags = db.query(models.Tag).filter(
        models.Tag.name.ilike(f"%{query}%")
    ).all()
    
    # 查询标签在任务中的使用计数
    task_tag_counts = db.query(
        models.TaskTag.tag_id, 
        func.count(models.TaskTag.task_id).label('count')
    ).group_by(models.TaskTag.tag_id).all()
    
    # 查询标签在笔记中的使用计数
    note_tag_counts = db.query(
        models.NoteTag.tag_id, 
        func.count(models.NoteTag.note_id).label('count')
    ).group_by(models.NoteTag.tag_id).all()
    
    # 转换为字典方便查找
    task_count_map = {tag_id: count for tag_id, count in task_tag_counts}
    note_count_map = {tag_id: count for tag_id, count in note_tag_counts}
    
    result = []
    for tag in tags:
        task_count = task_count_map.get(tag.id, 0)
        note_count = note_count_map.get(tag.id, 0)
        result.append({
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "count": task_count + note_count,  # 总计数
            "task_count": task_count,
            "note_count": note_count
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
    # 删除关联的笔记-标签关系
    db.query(models.NoteTag).filter(models.NoteTag.tag_id == tag_id).delete()
    # 再删除标签
    db.delete(db_tag)
    db.commit()
    return True