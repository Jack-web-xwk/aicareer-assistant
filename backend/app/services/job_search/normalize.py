"""
将 RawJobRow / 字典映射为 API 层的 UnifiedJobItem。
"""

from app.models.job_search_schemas import JobSource, UnifiedJobItem
from app.services.job_search.types import RawJobRow


def raw_row_to_unified(row: RawJobRow, source: JobSource) -> UnifiedJobItem:
    return UnifiedJobItem(
        title=row.title.strip() or "（无标题）",
        company_name=row.company_name.strip(),
        salary_text=row.salary_text.strip(),
        location=row.location.strip(),
        published_at=row.published_at,
        experience_text=row.experience_text.strip(),
        education_text=row.education_text.strip(),
        source=source,
        detail_url=row.detail_url.strip(),
        raw_snippet=row.raw_snippet,
    )
