"""
Logger - 日志配置

提供统一的日志配置和获取函数。
"""

import logging
import sys
from typing import Optional

from app.core.config import settings


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取配置好的 Logger 实例
    
    Args:
        name: Logger 名称，默认使用模块名
    
    Returns:
        Logger 实例
    """
    logger = logging.getLogger(name or __name__)
    
    # 避免重复配置
    if logger.handlers:
        return logger
    
    # 设置日志级别
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    logger.setLevel(log_level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # 设置格式
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    
    # 防止日志传播到根 logger
    logger.propagate = False
    
    return logger


# 创建默认 logger
default_logger = get_logger("ai_career_assistant")
