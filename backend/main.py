"""
AI Career Assistant - FastAPI Application Entry Point

基于 FastAPI + LangGraph 的 AI 求职助手后端服务入口
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import create_tables, ensure_sqlite_schema
from app.services.resume_optimization_job import recover_resume_optimizations_on_startup
from app.core.exception_handlers import register_exception_handlers
from app.api import router as api_router
from app.utils.logger import get_logger

# 初始化日志
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    - 启动时：初始化数据库、创建必要目录
    - 关闭时：清理资源
    """
    # Startup: 创建数据库表
    logger.info("开始初始化数据库表")
    await create_tables()
    await ensure_sqlite_schema()
    logger.info("数据库表初始化完成")
    
    # Startup: 创建上传目录
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"上传目录创建完成: {upload_dir}")
    
    # Startup: 创建数据目录
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"数据目录创建完成: {data_dir}")
    
    await recover_resume_optimizations_on_startup()
    
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started!")
    logger.info(f"📚 API Docs: http://localhost:8000/docs")
    
    yield
    
    # Shutdown: 清理资源
    logger.info(f"👋 {settings.APP_NAME} shutting down...")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    description="基于 FastAPI + LangGraph 的 AI 求职助手，提供简历智能优化和语音技术面试模拟功能。",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常日志（所有路由未捕获异常、HTTPException、422 均落盘）
register_exception_handlers(app)

# 注册 API 路由
app.include_router(api_router, prefix="/api")

# 挂载静态文件目录（用于上传文件访问）
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/", tags=["Root"])
async def root():
    """
    根路由 - 返回 API 基本信息
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "AI 求职助手 API",
        "docs": "/docs",
        "health": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
