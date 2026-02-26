"""
Text Utilities - 文本处理工具

提供文本操作相关的工具函数。
"""

import json
import re
from typing import Any, Optional


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    截断文本到指定长度
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后的后缀
    
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_json_from_text(text: str) -> Optional[Any]:
    """
    从文本中提取 JSON 内容
    
    支持从 ```json ... ``` 代码块中提取。
    
    Args:
        text: 包含 JSON 的文本
    
    Returns:
        解析后的 JSON 对象，失败返回 None
    """
    # 尝试从代码块中提取
    patterns = [
        r'```json\s*([\s\S]*?)\s*```',  # ```json ... ```
        r'```\s*([\s\S]*?)\s*```',       # ``` ... ```
        r'\{[\s\S]*\}',                   # {...}
        r'\[[\s\S]*\]',                   # [...]
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            json_str = match.group(1) if match.lastindex else match.group(0)
            try:
                return json.loads(json_str.strip())
            except json.JSONDecodeError:
                continue
    
    # 直接尝试解析整个文本
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return None


def clean_markdown(text: str) -> str:
    """
    清理 Markdown 格式，提取纯文本
    
    Args:
        text: Markdown 文本
    
    Returns:
        纯文本
    """
    # 移除代码块
    text = re.sub(r'```[\s\S]*?```', '', text)
    # 移除行内代码
    text = re.sub(r'`[^`]+`', '', text)
    # 移除链接
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # 移除图片
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
    # 移除标题符号
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # 移除加粗/斜体
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    # 移除列表符号
    text = re.sub(r'^[\-\*\+]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s*', '', text, flags=re.MULTILINE)
    # 清理多余空白
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def normalize_whitespace(text: str) -> str:
    """
    规范化空白字符
    
    Args:
        text: 原始文本
    
    Returns:
        规范化后的文本
    """
    # 替换各种空白字符为标准空格
    text = re.sub(r'[\t\r\f\v]+', ' ', text)
    # 合并多个空格
    text = re.sub(r' {2,}', ' ', text)
    # 清理行首行尾空白
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join(lines)


def count_words(text: str) -> int:
    """
    统计文本中的单词/字符数
    
    对于中文，统计字符数；对于英文，统计单词数。
    
    Args:
        text: 文本
    
    Returns:
        单词/字符数
    """
    # 统计中文字符
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # 统计英文单词
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
    
    return chinese_chars + english_words
