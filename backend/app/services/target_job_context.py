"""
目标岗位上下文：支持「链接爬取」与「截图保存的 job:screenshot: 伪链接」两种来源，写入 Resume / 优化任务。
"""

from __future__ import annotations

import json
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.models.saved_job import SavedJob
from app.models.schemas import JobRequirements
from app.services.job_posting_text import job_desc_text_from_requirements, job_snapshot_json
from app.services.job_scraper import scrape_job_info
from app.utils.logger import get_logger

logger = get_logger(__name__)

SCREENSHOT_JOB_URL_PREFIX = "job:screenshot:"


def is_screenshot_job_url(job_url: str) -> bool:
    return bool(job_url and job_url.startswith(SCREENSHOT_JOB_URL_PREFIX))


def new_screenshot_job_url() -> str:
    return f"{SCREENSHOT_JOB_URL_PREFIX}{uuid.uuid4().hex}"


async def load_saved_job_requirements(
    session: AsyncSession,
    user_id: int,
    job_url: str,
) -> Optional[JobRequirements]:
    """从 saved_jobs.raw_snippet 解析 JobRequirements；不存在则 None。"""
    if not is_screenshot_job_url(job_url):
        return None
    result = await session.execute(
        select(SavedJob).where(
            SavedJob.user_id == user_id,
            SavedJob.detail_url == job_url,
        )
    )
    row = result.scalar_one_or_none()
    if not row or not (row.raw_snippet or "").strip():
        return None
    try:
        data = json.loads(row.raw_snippet)
        return JobRequirements.model_validate(data)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("saved_job raw_snippet 解析失败 id=%s: %s", row.id, e)
        return None


async def apply_target_job_to_resume_row(
    session: AsyncSession,
    resume: Resume,
    user_id: int,
    job_url: str,
) -> str:
    """
    根据 job_url 写入 resume 的 target_job_title / job_description / job_snapshot。
    返回用于优化的岗位说明文本 job_desc。
    """
    if is_screenshot_job_url(job_url):
        jr = await load_saved_job_requirements(session, user_id, job_url)
        if not jr:
            raise ValueError(
                "未找到与该截图职位 ID 对应的保存记录，请先在「目标岗位」页上传截图并保存。"
            )
        job_desc = job_desc_text_from_requirements(jr, job_url)
        resume.target_job_title = jr.title
        resume.job_description = job_desc
        snap = jr.model_dump()
        snap["source_url"] = job_url
        snap["source"] = "screenshot"
        resume.job_snapshot = json.dumps(snap, ensure_ascii=False)
        return job_desc

    try:
        logger.info("爬取岗位信息: %s", job_url)
        job_info = scrape_job_info(job_url)
        job_desc = job_desc_text_from_requirements(job_info, job_url)
        resume.target_job_title = job_info.title
        resume.job_description = job_desc
        resume.job_snapshot = job_snapshot_json(job_info, job_url)
        logger.info("岗位信息爬取成功: %s", job_info.title)
        return job_desc
    except Exception as e:
        logger.error("岗位信息爬取失败: %s", str(e), exc_info=True)
        job_desc = f"目标岗位链接：{job_url}"
        resume.job_description = job_desc
        resume.job_snapshot = json.dumps(
            {"source_url": job_url, "scrape_error": str(e)},
            ensure_ascii=False,
        )
        return job_desc
