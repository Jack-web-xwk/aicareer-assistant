"""
Progress Dashboard API - 进度仪表板接口

提供用户进度统计、趋势数据、热力图数据等 API。
"""

import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.interview import InterviewRecord, InterviewStatus
from app.models.user import User
from app.models.schemas import SuccessResponse

router = APIRouter()


@router.get("/progress/stats", response_model=SuccessResponse)
async def get_progress_stats(
    user_id: Optional[int] = None,
    timeframe: str = "month",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取用户进度统计数据
    
    Args:
        user_id: 用户 ID（可选，默认当前用户）
        timeframe: 时间范围 (week/month/quarter/year)
    
    Returns:
        {
            "total_interviews": 总面试次数，
            "avg_score": 平均分，
            "dimensions": [
                {"dimension": "技术能力", "score": 85.5, "max_score": 100},
                ...
            ],
            "weekly_practice_count": 本周练习次数
        }
    """
    target_user_id = user_id or current_user.id
    
    # 计算时间范围
    now = datetime.utcnow()
    if timeframe == "week":
        days_delta = 7
    elif timeframe == "month":
        days_delta = 30
    elif timeframe == "quarter":
        days_delta = 90
    elif timeframe == "year":
        days_delta = 365
    else:
        days_delta = 30
    
    start_date = now - timedelta(days=days_delta)
    
    # 查询面试记录
    result = await db.execute(
        select(InterviewRecord)
        .where(
            and_(
                InterviewRecord.user_id == target_user_id,
                InterviewRecord.status == InterviewStatus.COMPLETED,
                InterviewRecord.started_at >= start_date,
            )
        )
    )
    records = result.scalars().all()
    
    # 计算统计数据
    total_interviews = len(records)
    avg_score = sum(r.total_score for r in records if r.total_score) / total_interviews if total_interviews > 0 else 0.0
    
    # 计算能力维度（从 dimension_scores 解析）
    # 前端期望的维度：technical_skill, communication, problem_solving, project_experience, cultural_fit
    dimensions_map = {
        "technical_depth": "technical_skill",
        "technical_breadth": "technical_skill", 
        "communication": "communication",
        "logic": "problem_solving",
        "problem_solving": "problem_solving",
    }
    
    dimension_totals = {}
    dimension_counts = {}
    
    for record in records:
        if record.dimension_scores:
            try:
                scores = json.loads(record.dimension_scores)
                for dim_item in scores:
                    dim_name = dim_item.get("name", "")
                    score = dim_item.get("score", 0)
                    
                    # 映射到前端维度
                    frontend_dim = dimensions_map.get(dim_name, dim_name)
                    
                    if frontend_dim not in dimension_totals:
                        dimension_totals[frontend_dim] = 0.0
                        dimension_counts[frontend_dim] = 0
                    
                    dimension_totals[frontend_dim] += score
                    dimension_counts[frontend_dim] += 1
            except (json.JSONDecodeError, AttributeError, TypeError):
                pass
    
    # 格式化维度数据（前端期望的 5 个维度）
    expected_dimensions = [
        ("technical_skill", "技术能力"),
        ("communication", "沟通能力"),
        ("problem_solving", "问题解决"),
        ("project_experience", "项目经验"),
        ("cultural_fit", "文化匹配"),
    ]
    
    radar_data = []
    for dim_key, dim_label in expected_dimensions:
        if dim_key in dimension_totals and dimension_counts[dim_key] > 0:
            avg = dimension_totals[dim_key] / dimension_counts[dim_key]
            radar_data.append({
                "dimension": dim_label,
                "score": round(avg, 1),
                "max_score": 100,
            })
        else:
            radar_data.append({
                "dimension": dim_label,
                "score": 0.0,
                "max_score": 100,
            })
    
    # 计算本周练习次数
    week_start = now - timedelta(days=7)
    week_result = await db.execute(
        select(func.count(InterviewRecord.id))
        .where(
            and_(
                InterviewRecord.user_id == target_user_id,
                InterviewRecord.started_at >= week_start,
            )
        )
    )
    weekly_practice_count = week_result.scalar() or 0
    
    return SuccessResponse(
        success=True,
        message="Progress stats retrieved successfully",
        data={
            "total_interviews": total_interviews,
            "avg_score": round(avg_score, 1),
            "dimensions": radar_data,
            "weekly_practice_count": weekly_practice_count,
        },
    )


@router.get("/progress/trend", response_model=SuccessResponse)
async def get_trend_data(
    user_id: Optional[int] = None,
    timeframe: str = "month",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取分数趋势数据
    
    Args:
        user_id: 用户 ID
        timeframe: 时间范围 (week/month/quarter/year)
    
    Returns:
        {
            "data": [
                {"date": "2026-03-31", "score": 85.5, "interview_count": 2},
                ...
            ]
        }
    """
    target_user_id = user_id or current_user.id
    
    # 计算时间范围
    now = datetime.utcnow()
    if timeframe == "week":
        days_delta = 7
    elif timeframe == "month":
        days_delta = 30
    elif timeframe == "quarter":
        days_delta = 90
    elif timeframe == "year":
        days_delta = 365
    else:
        days_delta = 30
    
    start_date = now - timedelta(days=days_delta)
    
    # 查询面试记录（按日期分组）
    result = await db.execute(
        select(
            func.date(InterviewRecord.started_at).label("date"),
            func.avg(InterviewRecord.total_score).label("avg_score"),
            func.count(InterviewRecord.id).label("count"),
        )
        .where(
            and_(
                InterviewRecord.user_id == target_user_id,
                InterviewRecord.status == InterviewStatus.COMPLETED,
                InterviewRecord.started_at >= start_date,
            )
        )
        .group_by(func.date(InterviewRecord.started_at))
        .order_by(func.date(InterviewRecord.started_at))
    )
    
    rows = result.all()
    
    trend_data = []
    for row in rows:
        if row.avg_score is not None:
            trend_data.append({
                "date": str(row.date),
                "score": round(row.avg_score, 1),
                "interview_count": row.count,
            })
    
    return SuccessResponse(
        success=True,
        message="Trend data retrieved successfully",
        data={
            "data": trend_data,
        },
    )


@router.get("/progress/heatmap", response_model=SuccessResponse)
async def get_heatmap_data(
    user_id: Optional[int] = None,
    month: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取练习热力图数据
    
    Args:
        user_id: 用户 ID
        month: 月份 (YYYY-MM 格式，可选，默认当前月)
    
    Returns:
        {
            "month": "2026-03",
            "days": [
                {"date": "2026-03-31", "count": 2, "intensity": 0.8},
                ...
            ],
            "total_practice_days": 15,
            "max_intensity": 5
        }
    """
    target_user_id = user_id or current_user.id
    
    # 解析月份
    if month:
        try:
            year, month_num = map(int, month.split("-"))
            month_start = datetime(year, month_num, 1)
            if month_num == 12:
                month_end = datetime(year + 1, 1, 1)
            else:
                month_end = datetime(year, month_num + 1, 1)
        except (ValueError, AttributeError):
            # 如果解析失败，使用当前月
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)
            if now.month == 12:
                month_end = datetime(now.year + 1, 1, 1)
            else:
                month_end = datetime(now.year, now.month + 1, 1)
            month = f"{now.year}-{now.month:02d}"
    else:
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        if now.month == 12:
            month_end = datetime(now.year + 1, 1, 1)
        else:
            month_end = datetime(now.year, now.month + 1, 1)
        month = f"{now.year}-{now.month:02d}"
    
    # 查询该月的面试记录（按日期分组）
    result = await db.execute(
        select(
            func.date(InterviewRecord.started_at).label("date"),
            func.count(InterviewRecord.id).label("count"),
        )
        .where(
            and_(
                InterviewRecord.user_id == target_user_id,
                InterviewRecord.started_at >= month_start,
                InterviewRecord.started_at < month_end,
            )
        )
        .group_by(func.date(InterviewRecord.started_at))
    )
    
    rows = result.all()
    
    # 构建热力图数据
    day_counts = {}
    max_count = 0
    
    for row in rows:
        date_str = str(row.date)
        count = row.count or 0
        day_counts[date_str] = count
        if count > max_count:
            max_count = count
    
    # 生成该月所有天的数据
    days = []
    if month_num == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month_num + 1
        next_year = year
    
    import calendar
    _, days_in_month = calendar.monthrange(year, month_num)
    
    for day in range(1, days_in_month + 1):
        date_str = f"{year}-{month_num:02d}-{day:02d}"
        count = day_counts.get(date_str, 0)
        intensity = count / max_count if max_count > 0 else 0.0
        
        days.append({
            "date": date_str,
            "count": count,
            "intensity": round(intensity, 2),
        })
    
    total_practice_days = sum(1 for d in days if d["count"] > 0)
    
    return SuccessResponse(
        success=True,
        message="Heatmap data retrieved successfully",
        data={
            "month": month,
            "days": days,
            "total_practice_days": total_practice_days,
            "max_intensity": max_count,
        },
    )
