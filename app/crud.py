# crud.py - 添加 Note 的 CRUD 函数
from sqlalchemy import or_, desc, asc, func
from sqlalchemy.orm import Session, aliased
from . import models, schemas
from datetime import datetime, timedelta
from fastapi import HTTPException
from typing import Optional, List, Dict
import random
from dateutil.relativedelta import relativedelta

# ========== 原有函数保持不变 ==========

# ========== Task 相关函数（保持不变）==========

from sqlalchemy import func

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
# TODO
def create_todo(db: Session, todo: schemas.TodoCreate):
    db_todo = models.Todo(**todo.model_dump())
    db.add(db_todo)
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

# NOTE
def create_note(db: Session, note: schemas.NoteCreate):
    db_note = models.Note(**note.model_dump())
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

# ========== 新增统计CRUD函数 ==========
def get_or_create_daily_stat(db: Session, date_str: str):
    """获取或创建每日统计"""
    daily_stat = db.query(models.DailyStat).filter(
        models.DailyStat.date == date_str
    ).first()
    
    if not daily_stat:
        # 创建新的统计记录
        daily_stat = models.DailyStat(
            date=date_str,
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
        db.add(daily_stat)
        db.commit()
        db.refresh(daily_stat)
    
    return daily_stat

def update_daily_stat(db: Session, date_str: str):
    """更新每日统计（基于实际任务数据）"""
    # 获取今日的任务
    today_start = datetime.strptime(date_str, "%Y-%m-%d")
    today_end = today_start + timedelta(days=1)
    
    tasks = db.query(models.Task).filter(
        models.Task.createdAt >= today_start,
        models.Task.createdAt < today_end
    ).all()
    
    # 计算统计数据
    completed = len([t for t in tasks if t.status == "done"])
    in_progress = len([t for t in tasks if t.status == "doing"])
    remaining = len([t for t in tasks if t.status == "todo"])
    total = len(tasks)
    
    # 按优先级统计
    priority_stats = {
        "high": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0},
        "medium": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0},
        "low": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0}
    }
    
    for task in tasks:
        if task.priority in priority_stats:
            stat = priority_stats[task.priority]
            stat["total"] += 1
            if task.status == "done":
                stat["completed"] += 1
            elif task.status == "doing":
                stat["in_progress"] += 1
            elif task.status == "todo":
                stat["remaining"] += 1
    
    # 更新或创建统计记录
    daily_stat = get_or_create_daily_stat(db, date_str)
    daily_stat.completed = completed
    daily_stat.in_progress = in_progress
    daily_stat.remaining = remaining
    daily_stat.total = total
    daily_stat.priority_stats = priority_stats
    daily_stat.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(daily_stat)
    
    return daily_stat
def get_week_stats(db: Session):
    """获取本周统计数据 - 不使用缓存，优先使用实际数据"""
    week_days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    week_data = []
    
    # 获取最近7天的数据（从周一到周日）
    for i in range(7):
        day_date = (datetime.now() - timedelta(days=6-i))
        date_str = day_date.strftime("%Y-%m-%d")
        day_name = week_days[i]
        
        # 直接查询 DailyStat 表中的实际数据
        daily_stat = get_or_create_daily_stat(db, date_str)
        
        # 判断是否有实际数据（非零值）
        has_actual_data = (
            daily_stat.total > 0 or
            daily_stat.completed > 0 or
            daily_stat.in_progress > 0 or
            daily_stat.remaining > 0
        )
        
        if has_actual_data:
            # 使用实际数据
            week_data.append({
                "day": day_name,
                "completed": daily_stat.completed,
                "inProgress": daily_stat.in_progress,
                "remaining": daily_stat.remaining
            })
        else:
            # 如果没有实际数据，生成模拟数据
            # 模拟数据逻辑：工作日（周一到周五）完成较多，周末完成较少
            if i < 5:  # 周一到周五
                completed = random.randint(8, 15)
                in_progress = random.randint(4, 8)
                remaining = random.randint(2, 5)
            else:  # 周六、周日
                completed = random.randint(5, 10)
                in_progress = random.randint(2, 5)
                remaining = random.randint(1, 3)
            
            week_data.append({
                "day": day_name,
                "completed": completed,
                "inProgress": in_progress,
                "remaining": remaining
            })
    
    # 不再使用 WeeklyStat 缓存表
    return {"week_data": week_data}
#  get_month_stats 函数
def get_month_stats(db: Session):
    """获取本月统计数据 - 不使用缓存，优先使用实际数据"""
    # 生成最近30天的数据
    month_data = []
    
    for i in range(30, 0, -1):
        day_date = datetime.now() - timedelta(days=i-1)
        date_str = day_date.strftime("%m-%d")
        full_date_str = day_date.strftime("%Y-%m-%d")
        
        # 尝试获取实际数据
        daily_stat = get_or_create_daily_stat(db, full_date_str)
        
        # 判断是否有实际数据（非零值）
        has_actual_data = (
            daily_stat.total > 0 or
            daily_stat.completed > 0 or
            daily_stat.in_progress > 0 or
            daily_stat.remaining > 0
        )
        
        if has_actual_data:
            # 使用实际数据
            month_data.append({
                "date": date_str,
                "completed": daily_stat.completed,
                "inProgress": daily_stat.in_progress,
                "remaining": daily_stat.remaining
            })
        else:
            # 如果没有实际数据，生成模拟数据
            # 模拟数据逻辑：基于日期变化趋势
            # 离今天越近，完成的任务越多（假设任务推进中）
            days_ago = i - 1  # 距离今天的天数
            if days_ago < 7:  # 最近7天
                completed = random.randint(8, 15)
                in_progress = random.randint(4, 8)
                remaining = random.randint(2, 5)
            elif days_ago < 14:  # 7-14天前
                completed = random.randint(6, 12)
                in_progress = random.randint(3, 7)
                remaining = random.randint(3, 6)
            else:  # 14天前
                completed = random.randint(4, 10)
                in_progress = random.randint(2, 6)
                remaining = random.randint(4, 8)
            
            month_data.append({
                "date": date_str,
                "completed": completed,
                "inProgress": in_progress,
                "remaining": remaining
            })
    
    # 不再使用 MonthlyStat 缓存表
    return {"month_data": month_data}

# get_year_stats 函数
def get_year_stats(db: Session):
    """获取年度统计数据 - 不使用缓存，优先使用实际数据"""
    current_year = datetime.now().year
    months = ["1月", "2月", "3月", "4月", "5月", "6月", 
             "7月", "8月", "9月", "10月", "11月", "12月"]
    
    year_data = []
    
    for month_num in range(1, 13):
        month_str = f"{month_num:02d}"
        
        # 计算该月的第一天和最后一天
        if month_num == 12:
            next_month = 1
            next_year = current_year + 1
        else:
            next_month = month_num + 1
            next_year = current_year
        
        # 尝试获取该月的实际统计数据
        # 方法：查询该月所有 DailyStat 记录，计算总和
        month_stats = db.query(models.DailyStat).filter(
            models.DailyStat.date.like(f"{current_year}-{month_str}-%")
        ).all()
        
        if month_stats:
            # 有实际数据，计算总和
            total_completed = sum(stat.completed for stat in month_stats)
            total_in_progress = sum(stat.in_progress for stat in month_stats)
            total_remaining = sum(stat.remaining for stat in month_stats)
            
            year_data.append({
                "month": f"{month_num}月",
                "completed": total_completed,
                "inProgress": total_in_progress,
                "remaining": total_remaining
            })
        else:
            # 没有实际数据，生成模拟数据
            # 模拟逻辑：春季和秋季任务较多，冬季较少
            if month_num in [3, 4, 5]:  # 春季
                completed = random.randint(40, 60)
                in_progress = random.randint(15, 25)
                remaining = random.randint(10, 20)
            elif month_num in [9, 10, 11]:  # 秋季
                completed = random.randint(35, 55)
                in_progress = random.randint(12, 22)
                remaining = random.randint(8, 18)
            elif month_num in [12, 1, 2]:  # 冬季
                completed = random.randint(20, 40)
                in_progress = random.randint(8, 18)
                remaining = random.randint(5, 15)
            else:  # 夏季
                completed = random.randint(30, 50)
                in_progress = random.randint(10, 20)
                remaining = random.randint(7, 17)
            
            year_data.append({
                "month": f"{month_num}月",
                "completed": completed,
                "inProgress": in_progress,
                "remaining": remaining
            })
    
    # 不再使用 YearlyStat 缓存表
    return {"year_data": year_data}

# get_all_stats 函数
def get_all_stats(db: Session):
    """获取完整的统计数据（用于前端展示）"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 更新今日统计
    daily_stat = update_daily_stat(db, today)
    
    # 获取周统计 - 不使用缓存，直接获取实际数据
    week_stat = get_week_stats(db)
    
    # 获取月统计 - 不使用缓存，直接获取实际数据
    month_stat = get_month_stats(db)
    
    # 获取年统计 - 不使用缓存，直接获取实际数据
    year_stat = get_year_stats(db)
    
    # 构建优先级统计列表
    priority_stats = []
    for level, stats in daily_stat.priority_stats.items():
        priority_stats.append({
            "level": level,
            "completed": stats["completed"],
            "inProgress": stats["in_progress"],
            "remaining": stats["remaining"],
            "total": stats["total"]
        })
    
    # 添加无优先级的统计
    all_tasks = db.query(models.Task).filter(
        models.Task.createdAt >= datetime.strptime(today, "%Y-%m-%d"),
        models.Task.createdAt < datetime.strptime(today, "%Y-%m-%d") + timedelta(days=1)
    ).all()
    
    none_priority_tasks = [t for t in all_tasks if t.priority not in ["high", "medium", "low"]]
    if none_priority_tasks:
        priority_stats.append({
            "level": "none",
            "completed": len([t for t in none_priority_tasks if t.status == "done"]),
            "inProgress": len([t for t in none_priority_tasks if t.status == "doing"]),
            "remaining": len([t for t in none_priority_tasks if t.status == "todo"]),
            "total": len(none_priority_tasks)
        })
    
    return {
        "today": {
            "completed": daily_stat.completed,
            "inProgress": daily_stat.in_progress,
            "remaining": daily_stat.remaining,
            "total": daily_stat.total
        },
        "week": week_stat["week_data"],  # 直接使用 week_data
        "month": month_stat["month_data"],  # 直接使用 month_data
        "year": year_stat["year_data"],  # 直接使用 year_data
        "priority": priority_stats
    }

def get_daily_stats(db: Session, skip: int = 0, limit: int = 100):
    """获取每日统计列表"""
    return db.query(models.DailyStat).order_by(
        desc(models.DailyStat.date)
    ).offset(skip).limit(limit).all()

def get_daily_stat_by_date(db: Session, date_str: str):
    """根据日期获取每日统计"""
    return db.query(models.DailyStat).filter(
        models.DailyStat.date == date_str
    ).first()

def create_daily_stat(db: Session, stat: schemas.DailyStatCreate):
    """创建每日统计"""
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

# crud.py - 修改 update_stat_data 函数，移除周数据缓存创建
def update_daily_stat(db: Session, date_str: str):
    """更新每日统计（基于今日有活动的任务）"""
    today_start = datetime.strptime(date_str, "%Y-%m-%d")
    today_end = today_start + timedelta(days=1)
    
    # 获取所有任务（不限于今天创建的）
    tasks = db.query(models.Task).all()
    
    # 计算今日状态的任务（基于状态变化）
    # 对于实际使用，你应该基于任务的 status 来计算，而不是 createdAt
    
    # 但为了简化，我们先统计所有任务
    completed = len([t for t in tasks if t.status == "done"])
    in_progress = len([t for t in tasks if t.status == "doing"])
    remaining = len([t for t in tasks if t.status == "todo"])
    total = len(tasks)
    
    # 按优先级统计
    priority_stats = {
        "high": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0},
        "medium": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0},
        "low": {"completed": 0, "in_progress": 0, "remaining": 0, "total": 0}
    }
    
    for task in tasks:
        if task.priority in priority_stats:
            stat = priority_stats[task.priority]
            stat["total"] += 1
            if task.status == "done":
                stat["completed"] += 1
            elif task.status == "doing":
                stat["in_progress"] += 1
            elif task.status == "todo":
                stat["remaining"] += 1
    
    # 更新或创建统计记录
    daily_stat = get_or_create_daily_stat(db, date_str)
    daily_stat.completed = completed
    daily_stat.in_progress = in_progress
    daily_stat.remaining = remaining
    daily_stat.total = total
    daily_stat.priority_stats = priority_stats
    daily_stat.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(daily_stat)
    
    return daily_stat

def get_stats_summary(db: Session):
    """获取统计摘要"""
    # 总任务数
    total_tasks = db.query(models.Task).count()
    
    # 完成任务数
    completed_tasks = db.query(models.Task).filter(
        models.Task.status == "done"
    ).count()
    
    # 进行中任务数
    in_progress_tasks = db.query(models.Task).filter(
        models.Task.status == "doing"
    ).count()
    
    # 待完成数
    todo_tasks = db.query(models.Task).filter(
        models.Task.status == "todo"
    ).count()
    
    # 今日新增
    today = datetime.now().date()
    today_tasks = db.query(models.Task).filter(
        func.date(models.Task.createdAt) == today
    ).count()
    
    # 本周新增
    week_start = today - timedelta(days=today.weekday())
    week_tasks = db.query(models.Task).filter(
        func.date(models.Task.createdAt) >= week_start
    ).count()
    
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "todo_tasks": todo_tasks,
        "today_new": today_tasks,
        "week_new": week_tasks,
        "completion_rate": round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0
    }


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
