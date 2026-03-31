"""
Database Configuration - 数据库配置

使用 SQLAlchemy 2.0 异步引擎管理数据库连接和会话。
"""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import settings
import logging

_logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """
    SQLAlchemy ORM 基类
    
    所有模型类都应继承此基类。
    """
    pass


# 创建异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 调试模式下打印 SQL 语句
    future=True,
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def create_tables() -> None:
    """
    创建所有数据库表
    
    在应用启动时调用，确保所有表都已创建。
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def ensure_sqlite_schema() -> None:
    """
    SQLite 轻量迁移：为已存在的旧表补充 ORM 新增列。

    SQLAlchemy create_all 不会修改已有表结构，旧库会缺列导致 INSERT 失败。
    """
    url = (settings.DATABASE_URL or "").lower()
    if "sqlite" not in url:
        return

    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='resumes' LIMIT 1"
            )
        )
        if result.scalar_one_or_none() is None:
            return

        result = await conn.execute(text("PRAGMA table_info(resumes)"))
        rows = result.fetchall()
        column_names = {row[1] for row in rows}

        if "job_snapshot" not in column_names:
            await conn.execute(
                text("ALTER TABLE resumes ADD COLUMN job_snapshot TEXT")
            )
            _logger.info(
                "SQLite 已补充 resumes.job_snapshot 列（旧库自动迁移）"
            )


async def drop_tables() -> None:
    """
    删除所有数据库表
    
    仅用于测试或重置数据库。
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（依赖注入）
    
    用于 FastAPI 的 Depends，自动管理会话生命周期。
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
