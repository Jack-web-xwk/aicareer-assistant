"""
职位搜索（多源聚合）API 的请求/响应模型。
"""

from enum import Enum
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


class JobSource(str, Enum):
    """招聘数据来源"""

    BOSS = "boss"
    ZHAOPIN = "zhaopin"
    YUPAO = "yupao"
    LINK = "link"  # 用户粘贴详情页 URL 爬取入库
    SCREENSHOT = "screenshot"  # 用户上传截图，多模态模型抽取后入库


class MatchMode(str, Enum):
    """关键词匹配模式"""

    FUZZY = "fuzzy"
    EXACT = "exact"


class SortBy(str, Enum):
    """排序字段"""

    PUBLISHED_AT = "published_at"
    SALARY = "salary"


class SortOrder(str, Enum):
    DESC = "desc"
    ASC = "asc"


class UnifiedJobItem(BaseModel):
    """统一职位卡片字段（各平台映射后）"""

    title: str
    company_name: str = ""
    salary_text: str = ""
    location: str = ""
    published_at: Optional[str] = Field(None, description="原始或 ISO 时间字符串")
    experience_text: str = ""
    education_text: str = ""
    source: JobSource
    detail_url: str
    raw_snippet: Optional[str] = None


class JobSearchQuery(BaseModel):
    """职位搜索请求体"""

    keyword: str = Field("", description="职位关键词")
    company_keyword: str = Field("", description="公司名称关键词")
    match_mode: MatchMode = MatchMode.FUZZY
    city: Optional[str] = Field(None, description="城市名或平台城市编码，由后端解释")
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    experience: Optional[str] = Field(None, description="经验要求关键词，如 3-5年")
    sources: List[JobSource] = Field(
        default_factory=lambda: [
            JobSource.BOSS,
            JobSource.ZHAOPIN,
            JobSource.YUPAO,
        ],
        description="要查询的数据源（不含 link，link 仅用于 URL 爬取入库）",
    )
    sort_by: SortBy = SortBy.PUBLISHED_AT
    sort_order: SortOrder = SortOrder.DESC
    page: int = Field(1, ge=1)
    page_size: int = Field(15, ge=1, le=50)


class JobSearchResponse(BaseModel):
    """职位搜索响应 data 字段"""

    items: List[UnifiedJobItem]
    total: int
    page: int
    page_size: int
    sources_used: List[str] = Field(default_factory=list)
    cached: bool = False
    warning: Optional[str] = None


class ScrapeJobUrlRequest(BaseModel):
    """粘贴招聘详情页 URL，服务端爬取后写入 saved_jobs"""

    url: str = Field(..., min_length=8, description="岗位详情页 URL，如 Boss 直聘 job_detail 链接")


class SavedJobRecord(BaseModel):
    """数据库中已保存的职位（API 返回）"""

    id: int
    title: str
    company_name: str = ""
    salary_text: str = ""
    location: str = ""
    published_at: Optional[str] = None
    experience_text: str = ""
    education_text: str = ""
    source: JobSource
    detail_url: str
    raw_snippet: Optional[str] = None
    created_at: str
    updated_at: str
