from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db
from typing import Optional
from app import models

router = APIRouter(prefix="/api/tags", tags=["tags"])

# 获取所有标签及计数，支持搜索
@router.get("/", response_model=list[schemas.TagCountResponse])
def read_and_search_tags(
    q: Optional[str] = None,  
    db: Session = Depends(get_db)
):
    if q:
        return crud.search_tags(db, query=q)
    return crud.get_tags_with_counts(db)

@router.get("/", response_model=list[schemas.TagCountResponse])
def read_and_search_tags(
    q: Optional[str] = None,  
    db: Session = Depends(get_db)
):
    if q:
        return crud.search_tags(db, query=q)
    return crud.get_tags_with_counts(db)

# 新增标签
@router.post("/", response_model=schemas.Tag)
def create_new_tag(tag: schemas.TagCreate, db: Session = Depends(get_db)):
    # 检查标签是否已存在 (避免重复创建)
    db_tag = crud.get_tag_by_name(db, name=tag.name)
    if db_tag:
        # 如果已存在，直接返回它
        return db_tag
        
    return crud.create_tag(db, tag=tag)

@router.delete("/{tag_id}", response_model=dict)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    # 检查标签是否存在
    db_tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # 先删除关联的任务-标签关系
    db.query(models.TaskTag).filter(models.TaskTag.tag_id == tag_id).delete()
    # 再删除标签本身
    db.delete(db_tag)
    db.commit()
    
    return {"message": "Tag deleted successfully"}