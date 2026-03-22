"""
简历优化后台任务：与 HTTP 长连接解耦，进程退出后可根据数据库中的 optimizing 状态恢复执行。
"""

from __future__ import annotations

import asyncio
import json
from typing import Dict, Optional

from sqlalchemy import select

from app.agents.resume_optimizer_agent import ResumeOptimizerAgent
from app.core.config import settings
from app.core.database import async_session_maker
from app.models.resume import Resume, ResumeStatus
from app.services.target_job_context import apply_target_job_to_resume_row
from app.utils.logger import get_logger

logger = get_logger(__name__)

_optimization_locks: Dict[int, asyncio.Lock] = {}
_locks_registry_lock = asyncio.Lock()


async def get_resume_optimization_lock(resume_id: int) -> asyncio.Lock:
    """同一简历仅允许一个优化流程（SSE 或后台任务）并发执行。"""
    async with _locks_registry_lock:
        if resume_id not in _optimization_locks:
            _optimization_locks[resume_id] = asyncio.Lock()
        return _optimization_locks[resume_id]


async def run_resume_optimization_job(resume_id: int) -> None:
    """
    执行完整非流式优化（用于同步 API 入队与启动恢复）。
    要求调用方已把 status 置为 OPTIMIZING 且已持久化 job_description（若缺则在此补爬）。
    """
    lock = await get_resume_optimization_lock(resume_id)
    async with lock:
        async with async_session_maker() as session:
            resume = await session.get(Resume, resume_id)
            if not resume:
                return
            if resume.status != ResumeStatus.OPTIMIZING:
                logger.info(
                    "跳过优化: resume_id=%s 当前状态=%s",
                    resume_id,
                    resume.status,
                )
                return
            if not resume.original_text:
                resume.status = ResumeStatus.FAILED
                resume.error_message = "Resume has not been parsed. Please re-upload."
                await session.commit()
                return
            job_url = resume.target_job_url
            if not job_url:
                resume.status = ResumeStatus.FAILED
                resume.error_message = "Target job URL is required for optimization"
                await session.commit()
                return

            job_desc: Optional[str] = resume.job_description
            if not job_desc or not str(job_desc).strip():
                await apply_target_job_to_resume_row(
                    session, resume, resume.user_id, job_url
                )
                await session.commit()

            job_desc = resume.job_description or job_desc or ""

            try:
                agent = ResumeOptimizerAgent()
                result_state = await agent.run(
                    resume_text=resume.original_text,
                    job_desc=job_desc,
                    job_url=job_url,
                )
            except Exception as e:
                logger.error(
                    "简历优化任务异常: resume_id=%s, error=%s",
                    resume_id,
                    str(e),
                    exc_info=True,
                )
                await session.refresh(resume)
                if resume.status != ResumeStatus.OPTIMIZING:
                    return
                resume.status = ResumeStatus.FAILED
                resume.error_message = str(e)
                await session.commit()
                return

            await session.refresh(resume)
            if resume.status != ResumeStatus.OPTIMIZING:
                logger.info(
                    "优化已完成或状态已变更，跳过写回: resume_id=%s status=%s",
                    resume_id,
                    resume.status,
                )
                return

            if result_state.get("error"):
                error_msg = result_state["error"]
                resume.status = ResumeStatus.FAILED
                resume.error_message = error_msg
                logger.error(
                    "简历优化失败: resume_id=%s, error=%s",
                    resume_id,
                    error_msg,
                )
            else:
                resume.status = ResumeStatus.OPTIMIZED
                resume.extracted_info = json.dumps(
                    result_state.get("extracted_info", {}),
                    ensure_ascii=False,
                )
                resume.match_analysis = json.dumps(
                    result_state.get("matched_content", {}),
                    ensure_ascii=False,
                )
                resume.optimized_resume = result_state.get("optimized_resume", "")
                logger.info("简历优化成功: resume_id=%s", resume_id)

            await session.commit()


def schedule_resume_optimization(resume_id: int) -> None:
    """在当前运行中的事件循环里投递后台优化任务。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.warning("无运行中的事件循环，无法调度简历优化: resume_id=%s", resume_id)
        return

    async def _wrapper() -> None:
        try:
            await run_resume_optimization_job(resume_id)
        except Exception:
            logger.exception("简历优化后台任务未捕获异常: resume_id=%s", resume_id)

    loop.create_task(_wrapper())


async def recover_resume_optimizations_on_startup() -> None:
    """启动时扫描仍为「优化中」的记录并继续执行（依赖已持久化的岗位描述等上下文）。"""
    if not settings.RESUME_OPTIMIZATION_RECOVERY_ON_STARTUP:
        return
    async with async_session_maker() as session:
        result = await session.execute(
            select(Resume.id).where(Resume.status == ResumeStatus.OPTIMIZING)
        )
        ids = list(result.scalars().all())
    if not ids:
        return
    logger.info("检测到未完成的简历优化任务，将恢复执行: resume_ids=%s", ids)
    for rid in ids:
        schedule_resume_optimization(rid)
