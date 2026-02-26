"""
Health Check API - 健康检查接口

提供服务健康状态检查。
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.schemas import SuccessResponse

router = APIRouter()


@router.get("", response_model=SuccessResponse)
async def health_check():
    """
    基础健康检查
    
    返回服务基本状态和版本信息。
    """
    return SuccessResponse(
        success=True,
        message="Service is healthy",
        data={
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@router.get("/db", response_model=SuccessResponse)
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """
    数据库健康检查
    
    检查数据库连接是否正常。
    """
    try:
        # 执行简单查询测试数据库连接
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        
        return SuccessResponse(
            success=True,
            message="Database connection is healthy",
            data={
                "database": "connected",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception as e:
        return SuccessResponse(
            success=False,
            message=f"Database connection failed: {str(e)}",
            data={
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@router.get("/ready", response_model=SuccessResponse)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    就绪检查
    
    检查服务是否准备好接收请求。
    """
    checks = {
        "database": False,
        "openai_api_key": False,
    }
    
    # 检查数据库
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        checks["database"] = True
    except Exception:
        pass
    
    # 检查 OpenAI API Key
    checks["openai_api_key"] = bool(settings.OPENAI_API_KEY)
    
    all_ready = all(checks.values())
    
    return SuccessResponse(
        success=all_ready,
        message="Service is ready" if all_ready else "Service is not fully ready",
        data={
            "ready": all_ready,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
