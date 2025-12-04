# crud.py
from sqlalchemy.orm import Session
from datetime import datetime
import models, schemas

# 1. 获取所有任务
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
    
    # 如果传了标签ID，关联标签（先简化：暂不处理标签，后续可扩展）
    # 这里先返回基础任务信息，标签功能可后续补充
    return get_task(db, db_task.id)

# 4. 更新任务
def update_task(db: Session, task_id: int, task: schemas.TaskUpdate):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        return None
    # 只更新传了值的字段
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