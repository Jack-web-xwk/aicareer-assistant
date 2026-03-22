"""
API Routes - API 路由

汇总所有 API 路由。
"""

from fastapi import APIRouter

from .health import router as health_router
from .resume import router as resume_router
from .interview import router as interview_router
from .jobs import router as jobs_router
from .learn import router as learn_router

# 创建主路由
router = APIRouter()

# 注册子路由
router.include_router(health_router, prefix="/health", tags=["Health"])
router.include_router(resume_router, prefix="/resume", tags=["Resume"])
router.include_router(interview_router, prefix="/interview", tags=["Interview"])
router.include_router(jobs_router, prefix="/jobs", tags=["Jobs"])
router.include_router(learn_router, prefix="/learn", tags=["Learn"])

__all__ = ["router"]
