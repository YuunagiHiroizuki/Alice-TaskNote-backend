from sqlalchemy.orm import Session, aliased, joinedload 
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
    db.commit()  # 添加这行
    db.refresh(db_task)  # 添加这行

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
    
# TODO


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
    update_data = note_update.model_dump(exclude_unset=True)  # 改为 model_dump
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
            "priority": note.priority.value if note.priority else "none", 
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
# ========== 统计相关函数 ==========

def get_all_stats(db: Session):
    """获取完整的统计数据"""
    # 获取今日统计
    today = datetime.now().strftime("%Y-%m-%d")
    today_stat = update_daily_stat(db, today)
    
    # 获取周统计
    week_stat = get_week_stats(db)
    
    # 获取月统计
    month_stat = get_month_stats(db)
    
    # 获取年统计
    year_stat = get_year_stats(db)
    
    # 获取优先级统计
    priority_stats = []
    if today_stat and today_stat.priority_stats:
        for level, stats in today_stat.priority_stats.items():
            priority_stats.append({
                "level": level,
                "completed": stats.get("completed", 0),
                "inProgress": stats.get("in_progress", 0),
                "remaining": stats.get("remaining", 0),
                "total": stats.get("total", 0)
            })
    
    return {
        "today": {
            "completed": today_stat.completed if today_stat else 0,
            "inProgress": today_stat.in_progress if today_stat else 0,
            "remaining": today_stat.remaining if today_stat else 0,
            "total": today_stat.total if today_stat else 0
        },
        "week": week_stat.get("week_data", []) if isinstance(week_stat, dict) else [],
        "month": month_stat.get("month_data", []) if isinstance(month_stat, dict) else [],
        "year": year_stat.get("year_data", []) if isinstance(year_stat, dict) else [],
        "priority": priority_stats
    }

def update_stat_data(db: Session):
    """更新统计数据的辅助函数"""
    today = datetime.now().strftime("%Y-%m-%d")
    return update_daily_stat(db, today)

def get_or_create_daily_stat(db: Session, date: str):
    """获取或创建每日统计"""
    stat = db.query(models.DailyStat).filter(models.DailyStat.date == date).first()
    if not stat:
        # 创建新的统计记录
        stat = models.DailyStat(
            date=date,
            completed=0,
            in_progress=0,
            remaining=0,
            total=0,
            priority_stats={
                "high": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0},
                "medium": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0},
                "low": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0}
            }
        )
        db.add(stat)
        db.commit()
        db.refresh(stat)
    return stat

def get_daily_stats(db: Session, skip: int = 0, limit: int = 100):
    """获取每日统计列表"""
    return db.query(models.DailyStat).order_by(desc(models.DailyStat.date)).offset(skip).limit(limit).all()

def get_daily_stat_by_date(db: Session, date: str):
    """根据日期获取每日统计"""
    return db.query(models.DailyStat).filter(models.DailyStat.date == date).first()

def create_daily_stat(db: Session, stat: schemas.DailyStatCreate):
    """创建每日统计记录"""
    db_stat = models.DailyStat(
        date=stat.date,
        completed=stat.completed,
        in_progress=stat.in_progress,
        remaining=stat.remaining,
        total=stat.total,
        priority_stats=stat.priority_stats or {
            "high": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0},
            "medium": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0},
            "low": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0}
        }
    )
    db.add(db_stat)
    db.commit()
    db.refresh(db_stat)
    return db_stat

def update_daily_stat(db: Session, date: str):
    """更新每日统计"""
    stat = get_or_create_daily_stat(db, date)
    
    # 计算任务统计
    tasks = db.query(models.Task).all()
    
    completed = 0
    in_progress = 0
    remaining = 0
    total = len(tasks)
    
    for task in tasks:
        if task.status == "done":
            completed += 1
        elif task.status == "doing":
            in_progress += 1
        elif task.status == "todo":
            remaining += 1
    
    # 更新统计
    stat.completed = completed
    stat.in_progress = in_progress
    stat.remaining = remaining
    stat.total = total
    
    # 更新优先级统计
    priority_stats = {
        "high": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0},
        "medium": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0},
        "low": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0}
    }
    
    for task in tasks:
        priority = task.priority
        if priority in ["high", "medium", "low"]:
            if task.status == "done":
                priority_stats[priority]["completed"] += 1
            elif task.status == "doing":
                priority_stats[priority]["in_progress"] += 1
            elif task.status == "todo":
                priority_stats[priority]["remaining"] += 1
            priority_stats[priority]["total"] += 1
    
    stat.priority_stats = priority_stats
    stat.updated_at = datetime.now()
    
    db.commit()
    db.refresh(stat)
    return stat

def get_week_stats(db: Session):
    """获取本周数据"""
    # 模拟数据
    week_days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    week_data = []
    import random
    
    for day in week_days:
        week_data.append({
            "day": day,
            "completed": random.randint(5, 15),
            "inProgress": random.randint(3, 8),
            "remaining": random.randint(1, 5)
        })
    
    return {"week_data": week_data}

def get_month_stats(db: Session):
    """获取本月数据"""
    import random
    
    month_data = []
    for i in range(30):
        date_str = f"01-{i+1:02d}" if i < 30 else ""
        month_data.append({
            "date": date_str,
            "completed": random.randint(5, 20),
            "inProgress": random.randint(3, 15),
            "remaining": random.randint(1, 10)
        })
    
    return {"month_data": month_data}

def get_year_stats(db: Session):
    """获取年度数据"""
    months = ["1月", "2月", "3月", "4月", "5月", "6月", 
             "7月", "8月", "9月", "10月", "11月", "12月"]
    year_data = []
    
    for i, month in enumerate(months):
        year_data.append({
            "month": month,
            "completed": 30 + i * 8,
            "inProgress": 10 + i * 3,
            "remaining": 5 + i * 2
        })
    
    return {"year_data": year_data}

def get_stats_summary(db: Session):
    """获取统计摘要"""
    today = datetime.now().strftime("%Y-%m-%d")
    stat = update_daily_stat(db, today)
    
    return {
        "date": today,
        "completed": stat.completed,
        "in_progress": stat.in_progress,
        "remaining": stat.remaining,
        "total": stat.total
    }
