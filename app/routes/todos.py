from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db
from typing import Optional

router = APIRouter(prefix="/api/tasks", tags=["todos"])

# 1. 获取所有任务，支持搜索
@router.get("/", response_model=list[schemas.TaskResponse])
def read_and_search_tasks(
    q: Optional[str] = None,  
    db: Session = Depends(get_db)
):
    if q:
        return crud.search_tasks(db, query=q)
    return crud.get_tasks(db)

# 2. 获取单个任务
@router.get("/{task_id}", response_model=schemas.TaskResponse)
def read_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

# 3. 创建任务
@router.post("/", response_model=schemas.TaskResponse)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db=db, task=task)

# 4. 更新任务
@router.patch("/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    db_task = crud.update_task(db=db, task_id=task_id, task=task)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

# 5. 删除任务
@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    success = crud.delete_task(db=db, task_id=task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "message": "Task deleted successfully"}

