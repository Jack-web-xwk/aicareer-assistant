"""
Dependencies - 依赖注入

定义 FastAPI 的依赖注入函数。
"""

from typing import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .config import settings


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    
    对 get_db 的封装，用于依赖注入。
    """
    async for session in get_db():
        yield session


def get_openai_api_key() -> str:
    """
    获取 OpenAI API Key
    
    用于需要 API Key 的服务。
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured")
    return settings.OPENAI_API_KEY


def get_upload_dir() -> str:
    """获取上传目录路径"""
    return settings.UPLOAD_DIR


def get_max_upload_size() -> int:
    """获取最大上传文件大小（字节）"""
    return settings.max_upload_size_bytes


class RateLimiter:
    """
    简单的请求频率限制器
    
    用于限制 API 调用频率，防止滥用。
    """
    
    def __init__(self, calls: int = 10, period: int = 60):
        """
        初始化限流器
        
        Args:
            calls: 允许的调用次数
            period: 时间周期（秒）
        """
        self.calls = calls
        self.period = period
        self._requests: dict = {}
    
    async def __call__(self, request: Request) -> bool:
        """
        检查是否超过频率限制
        
        TODO: 实现基于 Redis 的分布式限流
        """
        # 简化实现，生产环境应使用 Redis
        return True
