"""
Core module - 核心配置和工具

包含应用配置、数据库连接、依赖注入和异常处理。
"""

from .config import settings
from .database import get_db, create_tables, ensure_sqlite_schema
from .exceptions import (
    AppException,
    NotFoundException,
    ValidationException,
    ExternalServiceException,
)

__all__ = [
    "settings",
    "get_db",
    "create_tables",
    "ensure_sqlite_schema",
    "AppException",
    "NotFoundException",
    "ValidationException",
    "ExternalServiceException",
]
