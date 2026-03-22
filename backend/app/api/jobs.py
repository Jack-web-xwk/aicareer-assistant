"""
职位搜索 API：多源聚合 + 缓存 + 限流；已保存职位持久化；URL 爬取入库。
"""

import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.resume import get_or_create_user
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import check_job_search_rate_limit
from app.models.job_search_schemas import (
    JobSearchQuery,
    JobSearchResponse,
    JobSource,
    SavedJobRecord,
    ScrapeJobUrlRequest,
    UnifiedJobItem,
)
from app.models.saved_job import SavedJob
from app.models.schemas import JobRequirements, SuccessResponse
from app.models.user import User
from app.services.job_search.aggregator import aggregate_jobs
from app.services.job_search.cache import cache_key, get_cached, set_cached
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _saved_job_to_record(row: SavedJob) -> SavedJobRecord:
    try:
        src = JobSource(row.source)
    except ValueError:
        src = JobSource.LINK
    return SavedJobRecord(
        id=row.id,
        title=row.title,
        company_name=row.company_name or "",
        salary_text=row.salary_text or "",
        location=row.location or "",
        published_at=row.published_at,
        experience_text=row.experience_text or "",
        education_text=row.education_text or "",
        source=src,
        detail_url=row.detail_url,
        raw_snippet=row.raw_snippet,
        created_at=row.created_at.isoformat(),
        updated_at=row.updated_at.isoformat(),
    )


def _job_requirements_to_unified(job: JobRequirements, url: str) -> UnifiedJobItem:
    """爬取结果 -> 与聚合列表一致的结构，便于写入 saved_jobs。"""
    return UnifiedJobItem(
        title=(job.title or "（无标题）").strip() or "（无标题）",
        company_name=(job.company or "").strip(),
        salary_text=(job.salary or "").strip(),
        location=(job.location or "").strip(),
        published_at=None,
        experience_text=(job.experience_years or "").strip(),
        education_text=(job.education_requirement or "").strip(),
        source=JobSource.LINK,
        detail_url=url.strip()[:1200],
        raw_snippet=json.dumps(job.model_dump(), ensure_ascii=False),
    )


async def _persist_unified_saved_job(
    db: AsyncSession,
    user: User,
    body: UnifiedJobItem,
) -> SavedJob:
    url = (body.detail_url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="detail_url 不能为空")

    result = await db.execute(
        select(SavedJob).where(
            SavedJob.user_id == user.id,
            SavedJob.detail_url == url,
        )
    )
    row = result.scalar_one_or_none()
    now = datetime.utcnow()
    payload = {
        "title": (body.title or "（无标题）")[:500],
        "company_name": (body.company_name or "")[:300],
        "salary_text": (body.salary_text or "")[:200],
        "location": (body.location or "")[:200],
        "published_at": (body.published_at or "")[:120] if body.published_at else None,
        "experience_text": (body.experience_text or "")[:200],
        "education_text": (body.education_text or "")[:200],
        "source": body.source.value,
        "detail_url": url[:1200],
        "raw_snippet": body.raw_snippet,
        "updated_at": now,
    }
    if row:
        for k, v in payload.items():
            setattr(row, k, v)
    else:
        row = SavedJob(
            user_id=user.id,
            created_at=now,
            updated_at=now,
            title=payload["title"],
            company_name=payload["company_name"],
            salary_text=payload["salary_text"],
            location=payload["location"],
            published_at=payload["published_at"],
            experience_text=payload["experience_text"],
            education_text=payload["education_text"],
            source=payload["source"],
            detail_url=payload["detail_url"],
            raw_snippet=payload["raw_snippet"],
        )
        db.add(row)

    await db.flush()
    await db.refresh(row)
    return row


def _cache_payload(query: JobSearchQuery) -> dict:
    d = query.model_dump(mode="json", exclude_none=True)
    if "sources" in d and isinstance(d["sources"], list):
        d["sources"] = sorted(d["sources"])
    return d


@router.post("/search", response_model=SuccessResponse)
def search_jobs(
    body: JobSearchQuery,
    _: None = Depends(check_job_search_rate_limit),
) -> SuccessResponse:
    """
    聚合 Boss / 智联 / 鱼泡 列表结果，进程内 TTL 缓存；单 IP 每分钟限流。
    """
    payload = _cache_payload(body)
    key = cache_key(payload)
    ttl = settings.JOB_SEARCH_CACHE_TTL_SECONDS

    cached = get_cached(key, ttl_seconds=ttl)
    if cached is not None:
        try:
            resp = JobSearchResponse.model_validate(cached)
            resp = resp.model_copy(update={"cached": True})
            return SuccessResponse(
                message="ok",
                data=resp.model_dump(mode="json"),
            )
        except Exception as e:
            logger.warning("缓存反序列化失败，重新拉取: %s", e)

    try:
        items, total, sources_used, warning = aggregate_jobs(body)
    except Exception as e:
        logger.exception("职位聚合失败: %s", e)
        resp = JobSearchResponse(
            items=[],
            total=0,
            page=body.page,
            page_size=body.page_size,
            sources_used=[],
            cached=False,
            warning=f"搜索失败: {e!s}",
        )
        return SuccessResponse(message="ok", data=resp.model_dump(mode="json"))

    resp = JobSearchResponse(
        items=items,
        total=total,
        page=body.page,
        page_size=body.page_size,
        sources_used=sources_used,
        cached=False,
        warning=warning,
    )
    set_cached(key, resp.model_dump(mode="json"))
    return SuccessResponse(message="ok", data=resp.model_dump(mode="json"))


@router.post("/saved", response_model=SuccessResponse)
async def save_job(
    body: UnifiedJobItem,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """将搜索结果中的职位保存到当前用户（同 URL 则更新）。"""
    user = await get_or_create_user(db)
    row = await _persist_unified_saved_job(db, user, body)
    return SuccessResponse(
        message="saved",
        data=_saved_job_to_record(row).model_dump(mode="json"),
    )


@router.post("/scrape-url", response_model=SuccessResponse)
async def scrape_job_url_and_save(
    body: ScrapeJobUrlRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(check_job_search_rate_limit),
) -> SuccessResponse:
    """
    用户粘贴目标岗位详情页 URL：爬取结构化信息并写入 saved_jobs（与「我的职位」同源）。
    计入职位类接口限流。
    """
    from app.services.job_scraper import scrape_job_info

    url = body.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="请输入以 http:// 或 https:// 开头的链接")

    loop = asyncio.get_running_loop()
    try:
        job_info = await loop.run_in_executor(None, scrape_job_info, url)
    except Exception as e:
        logger.exception("岗位 URL 爬取失败: %s", url)
        raise HTTPException(status_code=502, detail=f"抓取失败: {e!s}") from e

    item = _job_requirements_to_unified(job_info, url)
    user = await get_or_create_user(db)
    try:
        row = await _persist_unified_saved_job(db, user, item)
    except Exception as e:
        logger.exception(
            "scrape-url 写入 saved_jobs 失败 | user_id=%s url=%s",
            getattr(user, "id", None),
            url,
        )
        raise HTTPException(
            status_code=500,
            detail=f"保存职位失败: {e!s}",
        ) from e

    return SuccessResponse(
        message="scraped_and_saved",
        data={
            "saved": _saved_job_to_record(row).model_dump(mode="json"),
            "job_snapshot": job_info.model_dump(),
        },
    )


@router.get("/saved", response_model=SuccessResponse)
async def list_saved_jobs(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """当前用户已保存的职位列表。"""
    user = await get_or_create_user(db)
    count_q = await db.execute(
        select(func.count()).select_from(SavedJob).where(SavedJob.user_id == user.id)
    )
    total = int(count_q.scalar_one() or 0)

    result = await db.execute(
        select(SavedJob)
        .where(SavedJob.user_id == user.id)
        .order_by(SavedJob.updated_at.desc())
        .offset(skip)
        .limit(min(limit, 100))
    )
    rows = result.scalars().all()
    items = [_saved_job_to_record(r).model_dump(mode="json") for r in rows]
    return SuccessResponse(
        message="ok",
        data={"items": items, "total": total, "skip": skip, "limit": limit},
    )


@router.delete("/saved/{job_id}", response_model=SuccessResponse)
async def delete_saved_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    user = await get_or_create_user(db)
    result = await db.execute(
        select(SavedJob).where(SavedJob.id == job_id, SavedJob.user_id == user.id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Saved job not found")
    await db.execute(
        delete(SavedJob).where(
            SavedJob.id == job_id,
            SavedJob.user_id == user.id,
        )
    )
    return SuccessResponse(message="deleted", data={"id": job_id})
