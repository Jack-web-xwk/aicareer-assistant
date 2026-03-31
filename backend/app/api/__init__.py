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
from .question_bank import router as question_bank_router
from .auth import router as auth_router

# 创建主路由
router = APIRouter()

# 注册子路由
router.include_router(health_router, prefix="/health", tags=["Health"])
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(resume_router, prefix="/resume", tags=["Resume"])
router.include_router(interview_router, prefix="/interview", tags=["Interview"])
router.include_router(jobs_router, prefix="/jobs", tags=["Jobs"])
router.include_router(learn_router, prefix="/learn", tags=["Learn"])
router.include_router(question_bank_router, prefix="/question-bank", tags=["Question Bank"])

__all__ = ["router"]
