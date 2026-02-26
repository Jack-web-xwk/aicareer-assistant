"""
File Utilities - 文件处理工具

提供文件操作相关的工具函数。
"""

import uuid
from pathlib import Path
from typing import Union


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    确保目录存在，不存在则创建
    
    Args:
        path: 目录路径
    
    Returns:
        Path 对象
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_extension(filename: str) -> str:
    """
    获取文件扩展名（小写，不含点号）
    
    Args:
        filename: 文件名
    
    Returns:
        扩展名（如 'pdf', 'docx'）
    """
    ext = Path(filename).suffix.lower()
    return ext[1:] if ext.startswith('.') else ext


def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """
    生成唯一文件名
    
    Args:
        original_filename: 原始文件名
        prefix: 文件名前缀
    
    Returns:
        唯一文件名
    """
    ext = get_file_extension(original_filename)
    unique_id = str(uuid.uuid4())[:8]
    
    if prefix:
        return f"{prefix}_{unique_id}.{ext}"
    return f"{unique_id}.{ext}"


def safe_delete_file(path: Union[str, Path]) -> bool:
    """
    安全删除文件
    
    Args:
        path: 文件路径
    
    Returns:
        是否删除成功
    """
    try:
        path = Path(path)
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False
    except Exception:
        return False


def get_file_size_mb(path: Union[str, Path]) -> float:
    """
    获取文件大小（MB）
    
    Args:
        path: 文件路径
    
    Returns:
        文件大小（MB）
    """
    path = Path(path)
    if path.exists():
        return path.stat().st_size / (1024 * 1024)
    return 0.0
