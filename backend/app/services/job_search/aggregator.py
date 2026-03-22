"""
合并多源结果、去重、排序、全局分页切片。
"""

import re
from typing import Dict, List, Optional, Tuple

from app.models.job_search_schemas import (
    JobSearchQuery,
    JobSource,
    SortBy,
    SortOrder,
    UnifiedJobItem,
)
from app.services.job_search.boss_list import search_boss_jobs
from app.services.job_search.normalize import raw_row_to_unified
from app.services.job_search.types import RawJobRow
from app.services.job_search.yupao_list import search_yupao_jobs
from app.services.job_search.zhaopin_list import search_zhaopin_jobs
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _salary_sort_key(text: str) -> float:
    if not text:
        return 0.0
    nums = re.findall(r"(\d+(?:\.\d+)?)", text.replace("K", "000").replace("k", "000"))
    if not nums:
        return 0.0
    try:
        return float(nums[0])
    except ValueError:
        return 0.0


def _published_sort_key(item: UnifiedJobItem) -> float:
    if not item.published_at:
        return 0.0
    s = item.published_at
    if s.isdigit() and len(s) > 10:
        try:
            return float(s) / 1000.0
        except ValueError:
            pass
    if s.isdigit():
        try:
            return float(s)
        except ValueError:
            pass
    return 0.0


def aggregate_jobs(query: JobSearchQuery) -> Tuple[List[UnifiedJobItem], int, List[str], Optional[str]]:
    """
    各源拉取足够条数以支撑全局 page/page_size，合并去重排序后切片。

    返回 (当前页 items, total, sources_used, warning)
    """
    match_exact = query.match_mode.value == "exact"
    sources_used: List[str] = []
    warnings: List[str] = []
    all_rows: List[Tuple[RawJobRow, JobSource]] = []

    # 每源多取一些，便于去重后仍能覆盖当前全局页
    need = query.page * query.page_size
    fetch_size = min(100, max(query.page_size, need + query.page_size))

    for src in query.sources:
        try:
            if src == JobSource.BOSS:
                rows, _ = search_boss_jobs(
                    query.keyword,
                    query.company_keyword,
                    match_exact,
                    query.city,
                    1,
                    fetch_size,
                )
                for r in rows:
                    all_rows.append((r, JobSource.BOSS))
                sources_used.append("boss")
                if not rows:
                    warnings.append("Boss 未返回职位（可能被限流或关键词无结果）")
            elif src == JobSource.ZHAOPIN:
                rows, _ = search_zhaopin_jobs(
                    query.keyword,
                    query.company_keyword,
                    match_exact,
                    query.city,
                    1,
                    fetch_size,
                )
                for r in rows:
                    all_rows.append((r, JobSource.ZHAOPIN))
                sources_used.append("zhaopin")
                if not rows:
                    warnings.append("智联未解析到职位（页面结构可能变化）")
            elif src == JobSource.YUPAO:
                rows, _ = search_yupao_jobs(
                    query.keyword,
                    query.company_keyword,
                    match_exact,
                    query.city,
                    1,
                    fetch_size,
                )
                for r in rows:
                    all_rows.append((r, JobSource.YUPAO))
                sources_used.append("yupao")
                if not rows:
                    warnings.append("鱼泡未解析到职位（域名或页面可能变化）")
        except Exception as e:
            logger.warning("数据源 %s 异常: %s", src, e, exc_info=True)
            warnings.append(f"{src.value} 拉取异常: {e!s}")

    seen: Dict[str, UnifiedJobItem] = {}
    order: List[str] = []
    for row, source in all_rows:
        url = row.detail_url.strip()
        if not url:
            continue
        if url in seen:
            continue
        item = raw_row_to_unified(row, source)
        seen[url] = item
        order.append(url)

    items = [seen[u] for u in order]

    if query.experience and str(query.experience).strip():
        exp_kw = str(query.experience).strip()
        items = [
            i
            for i in items
            if exp_kw in (i.experience_text or "") or exp_kw in (i.title or "")
        ]

    reverse = query.sort_order == SortOrder.DESC
    if query.sort_by == SortBy.SALARY:
        items.sort(key=lambda x: _salary_sort_key(x.salary_text), reverse=reverse)
    else:
        items.sort(key=_published_sort_key, reverse=reverse)

    total = len(items)
    start = (query.page - 1) * query.page_size
    end = start + query.page_size
    page_items = items[start:end]

    warn = "；".join(warnings) if warnings else None
    return page_items, total, sources_used, warn
