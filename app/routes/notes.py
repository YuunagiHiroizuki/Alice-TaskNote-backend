# notes.py - 完整的笔记 API 路由
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/notes", tags=["Notes"])

# 获取笔记列表（支持搜索、筛选、排序）
@router.get("/", response_model=List[schemas.NoteResponse])
def read_notes(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="搜索关键词"),
    tags: Optional[List[int]] = Query(None, description="按标签ID筛选"),
    pinned: Optional[bool] = Query(None, description="是否置顶"),
    sort_by: Optional[str] = Query("updated_at", description="排序字段: title, created_at, updated_at, isPinned"),
    order: Optional[str] = Query("desc", description="排序顺序: asc, desc"),
    db: Session = Depends(get_db)
):
    """
    获取笔记列表，支持搜索、筛选和排序
    """
    return crud.get_notes(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        tag_ids=tags,
        pinned=pinned,
        sort_by=sort_by,
        order=order
    )

# 获取单个笔记
@router.get("/{note_id}", response_model=schemas.NoteResponse)
def read_note(note_id: int, db: Session = Depends(get_db)):
    """
    根据ID获取单个笔记
    """
    note = crud.get_note(db, note_id=note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

# 创建笔记
@router.post("/", response_model=schemas.NoteResponse)
def create_note(note: schemas.NoteCreate, db: Session = Depends(get_db)):
    """
    创建新笔记
    """
    return crud.create_note(db=db, note=note)

# 更新笔记
@router.put("/{note_id}", response_model=schemas.NoteResponse)
def update_note(note_id: int, note_update: schemas.NoteUpdate, db: Session = Depends(get_db)):
    """
    更新笔记信息
    """
    db_note = crud.update_note(db=db, note_id=note_id, note_update=note_update)
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return db_note

# 删除笔记
@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """
    删除笔记
    """
    success = crud.delete_note(db=db, note_id=note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"success": True, "message": "Note deleted successfully"}

# 搜索笔记
@router.get("/search/", response_model=List[schemas.NoteResponse])
def search_notes(
    q: Optional[str] = Query(None, description="搜索关键词"),
    tag: Optional[int] = Query(None, description="按标签ID搜索"),
    db: Session = Depends(get_db)
):
    """
    搜索笔记（按关键词或标签）
    """
    if not q and not tag:
        raise HTTPException(status_code=400, detail="Please provide search keyword or tag")
    
    return crud.search_notes(db=db, keyword=q, tag=tag)

# 切换置顶状态
@router.patch("/{note_id}/toggle-pin", response_model=schemas.NoteResponse)
def toggle_pin_note(note_id: int, db: Session = Depends(get_db)):
    """
    切换笔记的置顶状态
    """
    db_note = crud.toggle_pin_note(db=db, note_id=note_id)
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return db_note

# 更新笔记标签
@router.patch("/{note_id}/tags", response_model=schemas.NoteResponse)
def update_note_tags(
    note_id: int,
    tags: List[int],
    db: Session = Depends(get_db)
):
    """
    更新笔记的标签
    """
    note_update = schemas.NoteUpdate(tags=tags)
    db_note = crud.update_note(db=db, note_id=note_id, note_update=note_update)
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return db_note

# 批量操作
@router.post("/batch/delete")
def batch_delete_notes(
    note_ids: List[int],
    db: Session = Depends(get_db)
):
    """
    批量删除笔记
    """
    deleted_count = 0
    for note_id in note_ids:
        if crud.delete_note(db=db, note_id=note_id):
            deleted_count += 1
    
    return {
        "success": True,
        "message": f"Successfully deleted {deleted_count} notes",
        "deleted_count": deleted_count,
        "total_requested": len(note_ids)
    }