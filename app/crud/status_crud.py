from sqlalchemy.orm import Session, aliased, joinedload 
from .. import models, schemas
from datetime import datetime
from fastapi import HTTPException
from typing import Optional, List
from sqlalchemy import func,or_, desc, asc


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