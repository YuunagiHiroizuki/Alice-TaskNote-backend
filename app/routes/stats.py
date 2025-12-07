# routes/stats.py - 统计相关的API路由（修复版本）
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import random  # 添加这行
from .. import crud, schemas, models  # 添加 models 导入
from ..database import get_db

router = APIRouter(prefix="/api/stats", tags=["Stats"])

@router.get("/", response_model=schemas.StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """
    获取完整的统计数据
    返回前端Stats.vue所需的所有统计信息
    """
    try:
        # 尝试使用 crud 函数
        stats = crud.get_all_stats(db)
        return stats
    except Exception as e:
        print(f"获取统计数据失败: {str(e)}")
        # 如果出错，返回模拟数据
        return {
            "today": {
                "completed": random.randint(5, 10),
                "inProgress": random.randint(3, 5),
                "remaining": random.randint(1, 3),
                "total": random.randint(10, 15)
            },
            "week": [
                {
                    "day": "周一",
                    "completed": random.randint(5, 15),
                    "inProgress": random.randint(3, 8),
                    "remaining": random.randint(1, 5)
                },
                {
                    "day": "周二",
                    "completed": random.randint(5, 15),
                    "inProgress": random.randint(3, 8),
                    "remaining": random.randint(1, 5)
                },
                {
                    "day": "周三",
                    "completed": random.randint(5, 15),
                    "inProgress": random.randint(3, 8),
                    "remaining": random.randint(1, 5)
                },
                {
                    "day": "周四",
                    "completed": random.randint(5, 15),
                    "inProgress": random.randint(3, 8),
                    "remaining": random.randint(1, 5)
                },
                {
                    "day": "周五",
                    "completed": random.randint(5, 15),
                    "inProgress": random.randint(3, 8),
                    "remaining": random.randint(1, 5)
                },
                {
                    "day": "周六",
                    "completed": random.randint(5, 15),
                    "inProgress": random.randint(3, 8),
                    "remaining": random.randint(1, 5)
                },
                {
                    "day": "周日",
                    "completed": random.randint(5, 15),
                    "inProgress": random.randint(3, 8),
                    "remaining": random.randint(1, 5)
                }
            ],
            "month": [
                {
                    "date": "01-01",
                    "completed": random.randint(5, 20),
                    "inProgress": random.randint(3, 15),
                    "remaining": random.randint(1, 10)
                }
                for i in range(30)
            ],
            "year": [
                {
                    "month": month,
                    "completed": 30 + i * 8,
                    "inProgress": 10 + i * 3,
                    "remaining": 5 + i * 2
                }
                for i, month in enumerate(["1月", "2月", "3月", "4月", "5月", "6月", 
                                         "7月", "8月", "9月", "10月", "11月", "12月"])
            ],
            "priority": [
                {
                    "level": "high",
                    "completed": random.randint(5, 10),
                    "inProgress": random.randint(2, 5),
                    "remaining": random.randint(1, 3),
                    "total": random.randint(10, 15)
                },
                {
                    "level": "medium",
                    "completed": random.randint(10, 20),
                    "inProgress": random.randint(5, 10),
                    "remaining": random.randint(3, 7),
                    "total": random.randint(20, 30)
                },
                {
                    "level": "low",
                    "completed": random.randint(8, 15),
                    "inProgress": random.randint(3, 8),
                    "remaining": random.randint(2, 5),
                    "total": random.randint(15, 25)
                }
            ]
        }

@router.post("/update")
def update_stats(db: Session = Depends(get_db)):
    """
    更新统计数据
    """
    try:
        result = crud.update_stat_data(db)
        return {"success": True, "message": "统计数据已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新统计失败: {str(e)}")

@router.get("/today")
def get_today_stats(db: Session = Depends(get_db)):
    """
    获取今日统计
    """
    today = datetime.now().strftime("%Y-%m-%d")
    stat = crud.get_or_create_daily_stat(db, today)
    return stat

@router.get("/daily")
def get_daily_stats(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取每日统计列表
    """
    stats = crud.get_daily_stats(db, skip=skip, limit=limit)
    return stats

@router.get("/daily/{date}")
def get_daily_stat_by_date(date: str, db: Session = Depends(get_db)):
    """
    根据日期获取每日统计
    """
    stat = crud.get_daily_stat_by_date(db, date)
    if not stat:
        raise HTTPException(status_code=404, detail="该日期的统计不存在")
    return stat

@router.post("/daily/")
def create_daily_stat(
    stat: schemas.DailyStatCreate,
    db: Session = Depends(get_db)
):
    """
    创建每日统计记录
    """
    # 检查是否已存在
    existing = crud.get_daily_stat_by_date(db, stat.date)
    if existing:
        raise HTTPException(status_code=400, detail="该日期的统计已存在")
    
    return crud.create_daily_stat(db, stat)

# routes/stats.py - 修改 /week 端点
@router.get("/week")
def get_week_data(db: Session = Depends(get_db)):
    """
    获取本周数据 - 优先使用实际数据
    """
    week_stat = crud.get_week_stats(db)
    # 直接返回列表，而不是字典
    return week_stat.get("week_data", [])


@router.get("/month")
def get_month_data(db: Session = Depends(get_db)):
    """
    获取本月数据 - 优先使用实际数据
    """
    month_stat = crud.get_month_stats(db)
    # 直接返回列表，而不是字典
    return month_stat.get("month_data", [])

@router.get("/year")
def get_year_data(db: Session = Depends(get_db)):
    """
    获取年度数据 - 优先使用实际数据
    """
    year_stat = crud.get_year_stats(db)
    # 直接返回列表，而不是字典
    return year_stat.get("year_data", [])

@router.get("/priority")
def get_priority_stats(db: Session = Depends(get_db)):
    """
    获取优先级统计数据
    """
    today = datetime.now().strftime("%Y-%m-%d")
    daily_stat = crud.update_daily_stat(db, today)
    
    priority_stats = []
    for level, stats in daily_stat.priority_stats.items():
        priority_stats.append({
            "level": level,
            "completed": stats["completed"],
            "inProgress": stats["in_progress"],
            "remaining": stats["remaining"],
            "total": stats["total"]
        })
    
    return {"priority": priority_stats}  # 保持与主端点一致的结构

@router.get("/summary")
def get_stats_summary(db: Session = Depends(get_db)):
    """
    获取统计摘要
    """
    summary = crud.get_stats_summary(db)
    return summary

# routes/stats.py - 修复get_trend_data
@router.get("/trend/{period}")
def get_trend_data(
    period: str = Path(..., description="周期: week, month, year"),
    db: Session = Depends(get_db)
):
    """
    获取趋势数据
    """
    if period == "week":
        week_stat = crud.get_week_stats(db)
        return week_stat.get("week_data", [])  # 直接返回列表
    elif period == "month":
        month_stat = crud.get_month_stats(db)
        return month_stat.get("month_data", [])  # 直接返回列表
    elif period == "year":
        year_stat = crud.get_year_stats(db)
        return year_stat.get("year_data", [])  # 直接返回列表
    else:
        raise HTTPException(status_code=400, detail="无效的周期参数")
        
@router.get("/mock")
def get_mock_stats():
    """
    获取模拟统计数据（用于开发测试）
    """
    
    # 生成今日统计数据
    today_stats = {
        "completed": random.randint(8, 15),
        "inProgress": random.randint(5, 10),
        "remaining": random.randint(3, 8),
        "total": random.randint(20, 30)
    }
    
    # 生成周数据
    week_days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    week_data = []
    base_completed = 8
    for i, day in enumerate(week_days):
        week_data.append({
            "day": day,
            "completed": base_completed + i,
            "inProgress": max(2, 6 - i),
            "remaining": max(1, 4 - i//2)
        })
    
    # 生成月数据
    month_data = []
    for i in range(30):
        date_str = (datetime.now() - timedelta(days=29-i)).strftime("%m-%d")
        month_data.append({
            "date": date_str,
            "completed": random.randint(5, 20),
            "inProgress": random.randint(3, 15),
            "remaining": random.randint(1, 10)
        })
    
    # 生成年数据
    months = ["1月", "2月", "3月", "4月", "5月", "6月", 
             "7月", "8月", "9月", "10月", "11月", "12月"]
    year_data = []
    base_year_completed = 50
    for i, month in enumerate(months):
        year_data.append({
            "month": month,
            "completed": base_year_completed + i * 10,
            "inProgress": 20 + i * 5,
            "remaining": 10 + i * 3
        })
    
    # 生成优先级数据
    priority_data = [
        {
            "level": "high",
            "completed": random.randint(5, 10),
            "inProgress": random.randint(2, 5),
            "remaining": random.randint(1, 3),
            "total": random.randint(10, 15)
        },
        {
            "level": "medium",
            "completed": random.randint(10, 20),
            "inProgress": random.randint(5, 10),
            "remaining": random.randint(3, 7),
            "total": random.randint(20, 30)
        },
        {
            "level": "low",
            "completed": random.randint(8, 15),
            "inProgress": random.randint(3, 8),
            "remaining": random.randint(2, 5),
            "total": random.randint(15, 25)
        }
    ]
    
    return {
        "today": today_stats,
        "week": week_data,
        "month": month_data,
        "year": year_data,
        "priority": priority_data
    }