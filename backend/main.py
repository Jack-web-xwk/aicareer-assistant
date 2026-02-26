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
from app.core.database import create_tables
from app.api import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    - 启动时：初始化数据库、创建必要目录
    - 关闭时：清理资源
    """
    # Startup: 创建数据库表
    await create_tables()
    
    # Startup: 创建上传目录
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Startup: 创建数据目录
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started!")
    print(f"📚 API Docs: http://localhost:8000/docs")
    
    yield
    
    # Shutdown: 清理资源
    print(f"👋 {settings.APP_NAME} shutting down...")


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
