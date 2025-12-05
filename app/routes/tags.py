from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db
from typing import Optional

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