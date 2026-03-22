"""
内部爬虫/适配器使用的原始行结构（各源可不同）。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RawJobRow:
    """单条原始职位，适配器填充后由 normalize 转为 UnifiedJobItem"""

    title: str
    company_name: str
    salary_text: str
    location: str
    published_at: Optional[str]
    experience_text: str
    education_text: str
    detail_url: str
    raw_snippet: Optional[str] = None
