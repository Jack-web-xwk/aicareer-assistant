"""
Resume API - 简历相关接口

提供简历上传、解析、优化和下载功能。
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session_maker, get_db
from app.core.exceptions import FileProcessingException, NotFoundException
from app.models.resume import Resume, ResumeStatus
from app.models.user import User
from app.models.schemas import (
    ResumeResponse,
    OptimizedResumeResponse,
    SuccessResponse,
    ErrorResponse,
    ExtractedResumeInfo,
    MatchAnalysis,
)
from app.services.resume_parser import parse_resume_file
from app.services.resume_optimization_job import (
    get_resume_optimization_lock,
    schedule_resume_optimization,
)
from app.services.resume_study_qa import generate_resume_study_qa
from app.services.target_job_context import apply_target_job_to_resume_row
from app.agents.resume_optimizer_agent import ResumeOptimizerAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


async def get_or_create_user(db: AsyncSession, email: str = "default@example.com") -> User:
    """获取或创建默认用户（简化版，实际应该有完整的认证）"""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(email=email, username="Default User")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return user


# 必须放在 /{resume_id} 等动态路由之前，否则 "history" 会被当成路径参数并触发 int 校验失败（列表无法加载）
@router.get("/history", response_model=SuccessResponse)
async def list_optimization_history(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    简历任务总览：返回当前用户全部简历记录（上传、解析、待优化、优化中、已完成、失败）。
    按「优化中 > 解析中 > 上传 > 待优化 > 失败 > 已完成」优先级 + 更新时间倒序。
    不含完整正文，详情请用 GET /resume/{id}。
    """
    user = await get_or_create_user(db)

    count_result = await db.execute(
        select(func.count())
        .select_from(Resume)
        .where(Resume.user_id == user.id)
    )
    total = int(count_result.scalar_one() or 0)

    priority = case(
        (Resume.status == ResumeStatus.OPTIMIZING, 0),
        (Resume.status == ResumeStatus.PARSING, 1),
        (Resume.status == ResumeStatus.UPLOADED, 2),
        (Resume.status == ResumeStatus.PARSED, 3),
        (Resume.status == ResumeStatus.FAILED, 4),
        else_=5,
    )

    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == user.id)
        .order_by(priority, Resume.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = result.scalars().all()

    items = []
    for r in rows:
        match_score: Optional[int] = None
        if r.match_analysis:
            try:
                ma = json.loads(r.match_analysis)
                if isinstance(ma, dict) and "match_score" in ma:
                    match_score = int(ma["match_score"])
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        opt = r.optimized_resume or ""
        orig = r.original_text or ""
        if opt:
            preview = opt[:280].replace("\n", " ")
            if len(opt) > 280:
                preview += "…"
        elif orig:
            preview = orig[:280].replace("\n", " ")
            if len(orig) > 280:
                preview += "…"
        else:
            preview = None
        job_snapshot = None
        if r.job_snapshot:
            try:
                job_snapshot = json.loads(r.job_snapshot)
            except (json.JSONDecodeError, TypeError):
                job_snapshot = None
        items.append(
            {
                "id": r.id,
                "original_filename": r.original_filename,
                "file_type": r.file_type,
                "status": r.status.value,
                "target_job_title": r.target_job_title,
                "target_job_url": r.target_job_url,
                "match_score": match_score,
                "preview": preview or None,
                "job_snapshot": job_snapshot,
                "error_message": r.error_message,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat(),
            }
        )

    return SuccessResponse(
        success=True,
        message="Optimization history retrieved successfully",
        data={
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        },
    )


@router.post("/upload", response_model=SuccessResponse)
async def upload_resume(
    file: UploadFile = File(..., description="简历文件（PDF/Word）"),
    target_job_url: Optional[str] = Form(None, description="目标岗位链接"),
    db: AsyncSession = Depends(get_db),
):
    """
    上传简历文件
    
    支持 PDF 和 Word 格式，上传后自动解析。
    """
    logger.info(f"开始上传简历文件: {file.filename}")
    
    # 验证文件类型
    allowed_types = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/msword": "doc",
    }
    
    content_type = file.content_type
    if content_type not in allowed_types:
        logger.warning(f"不支持的文件类型: {content_type}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Allowed: PDF, DOCX",
        )
    
    file_type = allowed_types[content_type]
    logger.debug(f"文件类型: {file_type}")
    
    # 验证文件大小
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        logger.warning(f"文件过大: {len(content)/1024/1024:.2f}MB")
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )
    
    try:
        # 获取用户
        user = await get_or_create_user(db)
        logger.debug(f"获取用户: {user.email}")
        
        # 保存文件
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_id = str(uuid.uuid4())
        file_path = upload_dir / f"{file_id}.{file_type}"
        
        with open(file_path, "wb") as f:
            f.write(content)
        logger.debug(f"文件保存成功: {file_path}")
        
        # 解析简历
        try:
            logger.info("开始解析简历")
            resume_text = parse_resume_file(
                file_content=content,
                file_type=file_type,
            )
            parse_status = ResumeStatus.PARSED
            logger.info("简历解析成功")
        except Exception as e:
            logger.error(f"简历解析失败: {str(e)}", exc_info=True)
            resume_text = None
            parse_status = ResumeStatus.FAILED
        
        # 创建数据库记录
        resume = Resume(
            user_id=user.id,
            original_filename=file.filename,
            file_path=str(file_path),
            file_type=file_type,
            original_text=resume_text,
            target_job_url=target_job_url,
            status=parse_status,
        )
        
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        
        logger.info(f"简历上传成功，ID: {resume.id}")
        return SuccessResponse(
            success=True,
            message="Resume uploaded successfully",
            data={
                "id": resume.id,
                "filename": resume.original_filename,
                "file_type": resume.file_type,
                "status": resume.status.value,
                "text_preview": resume_text[:500] if resume_text else None,
                "created_at": resume.created_at.isoformat(),
            },
        )
    
    except Exception as e:
        logger.error(f"上传简历失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload resume: {str(e)}",
        )


@router.post("/optimize/{resume_id}", response_model=SuccessResponse, status_code=202)
async def optimize_resume(
    resume_id: int,
    target_job_url: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    优化简历（异步）

    立即返回 202，实际 LLM 优化在后台执行；可通过 GET /resume/{id} 轮询状态。
    服务重启后会自动恢复仍为「优化中」的任务。
    """
    logger.info(f"入队优化简历，ID: {resume_id}")

    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()

    if not resume:
        logger.warning(f"简历不存在，ID: {resume_id}")
        raise HTTPException(status_code=404, detail="Resume not found")

    job_url = target_job_url or resume.target_job_url

    if not job_url:
        logger.warning(f"目标岗位 URL 缺失，ID: {resume_id}")
        raise HTTPException(
            status_code=400,
            detail="Target job URL is required for optimization",
        )

    if not resume.original_text:
        logger.warning(f"简历未解析，ID: {resume_id}")
        raise HTTPException(
            status_code=400,
            detail="Resume has not been parsed. Please re-upload.",
        )

    user = await get_or_create_user(db)
    try:
        resume.status = ResumeStatus.OPTIMIZING
        resume.target_job_url = job_url
        await apply_target_job_to_resume_row(db, resume, user.id, job_url)
        await db.commit()
        await db.refresh(resume)
        logger.debug("已持久化 OPTIMIZING 与岗位上下文，ID: %s", resume_id)

        schedule_resume_optimization(resume_id)

        return SuccessResponse(
            success=True,
            message="Resume optimization queued; poll GET /resume/{id} for results",
            data={
                "id": resume.id,
                "status": resume.status.value,
                "target_job_title": resume.target_job_title,
                "updated_at": resume.updated_at.isoformat(),
            },
        )

    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"入队优化失败: {str(e)}", exc_info=True)
        resume.status = ResumeStatus.FAILED
        resume.error_message = str(e)
        await db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue resume optimization: {str(e)}",
        )


@router.post("/optimize/{resume_id}/stream")
async def optimize_resume_stream(
    resume_id: int,
    target_job_url: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    流式优化简历（SSE）。

    在生成器内持有每简历互斥锁并单独使用数据库会话，避免与后台恢复任务并发写同一行；
    爬取结果在流开始前写入库，进程中断后重启可依据 optimizing + job_description 继续跑后台任务。
    """
    logger.info(f"开始流式优化简历，resume_id={resume_id}")

    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    job_url = target_job_url or resume.target_job_url
    if not job_url:
        raise HTTPException(status_code=400, detail="Target job URL is required for optimization")
    if not resume.original_text:
        raise HTTPException(status_code=400, detail="Resume has not been parsed. Please re-upload.")

    async def event_generator() -> AsyncGenerator[str, None]:
        lock = await get_resume_optimization_lock(resume_id)
        async with lock:
            async with async_session_maker() as session:
                res = await session.execute(select(Resume).where(Resume.id == resume_id))
                r = res.scalar_one_or_none()
                if not r:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Resume not found'}, ensure_ascii=False)}\n\n"
                    return

                if r.status == ResumeStatus.OPTIMIZED and (
                    r.optimized_resume or r.match_analysis
                ):
                    try:
                        ei = json.loads(r.extracted_info or "{}")
                    except (json.JSONDecodeError, TypeError):
                        ei = {}
                    try:
                        ma = json.loads(r.match_analysis or "{}")
                    except (json.JSONDecodeError, TypeError):
                        ma = {}
                    done_payload = {
                        "type": "done",
                        "optimized_resume": r.optimized_resume or "",
                        "extracted_info": ei,
                        "match_analysis": ma,
                    }
                    yield f"data: {json.dumps(done_payload, ensure_ascii=False)}\n\n"
                    return

                r.status = ResumeStatus.OPTIMIZING
                r.target_job_url = job_url
                if not r.job_description or not str(r.job_description).strip():
                    try:
                        await apply_target_job_to_resume_row(
                            session, r, r.user_id, job_url
                        )
                    except ValueError as err:
                        yield f"data: {json.dumps({'type': 'error', 'message': str(err)}, ensure_ascii=False)}\n\n"
                        return
                await session.commit()
                await session.refresh(r)

                job_desc = r.job_description or f"目标岗位链接：{job_url}"

                agent = ResumeOptimizerAgent()
                final_extracted_info = None
                final_match_analysis = None
                final_optimized_resume = ""
                has_error = False

                try:
                    async for event in agent.run_stream(
                        resume_text=r.original_text or "",
                        job_desc=job_desc,
                        job_url=job_url,
                    ):
                        event_type = event.get("type")
                        if event_type == "done":
                            final_extracted_info = event.get("extracted_info")
                            final_match_analysis = event.get("match_analysis")
                            final_optimized_resume = event.get("optimized_resume", "")
                        elif event_type == "error":
                            has_error = True
                            r.status = ResumeStatus.FAILED
                            r.error_message = event.get("message", "Unknown stream error")
                            await session.commit()
                            logger.error(
                                "流式简历优化失败: resume_id=%s, error=%s",
                                resume_id,
                                r.error_message,
                            )

                        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

                    if not has_error:
                        await session.refresh(r)
                        if r.status != ResumeStatus.OPTIMIZING:
                            logger.info(
                                "流式优化结束时状态已变化 resume_id=%s status=%s",
                                resume_id,
                                r.status,
                            )
                            return
                        r.status = ResumeStatus.OPTIMIZED
                        r.extracted_info = json.dumps(
                            final_extracted_info or {}, ensure_ascii=False
                        )
                        r.match_analysis = json.dumps(
                            final_match_analysis or {}, ensure_ascii=False
                        )
                        r.optimized_resume = final_optimized_resume
                        await session.commit()
                        logger.info("流式简历优化完成，resume_id=%s", resume_id)
                except Exception as e:
                    logger.error(
                        "流式简历优化异常，resume_id=%s, error=%s",
                        resume_id,
                        str(e),
                        exc_info=True,
                    )
                    await session.refresh(r)
                    if r.status == ResumeStatus.OPTIMIZING:
                        r.status = ResumeStatus.FAILED
                        r.error_message = str(e)
                        await session.commit()
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{resume_id}/unlock-optimization", response_model=SuccessResponse)
async def unlock_resume_optimization(
    resume_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    将卡在「优化中」的任务恢复为「已解析」，便于重新发起流式优化（例如页面关闭导致 SSE 中断）。
    仅允许操作属于当前默认用户的简历。
    """
    user = await get_or_create_user(db)
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.status != ResumeStatus.OPTIMIZING:
        raise HTTPException(
            status_code=400,
            detail="当前任务不在「优化中」状态，无需解除",
        )
    resume.status = ResumeStatus.PARSED
    resume.error_message = None
    await db.commit()
    await db.refresh(resume)
    return SuccessResponse(
        success=True,
        message="已解除优化中状态，可重新发起优化",
        data={"id": resume.id, "status": resume.status.value},
    )


@router.post("/{resume_id}/study-qa", response_model=SuccessResponse)
async def generate_resume_study_qa_endpoint(
    resume_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    根据已完成优化的简历任务（岗位描述、匹配分析、优化稿）生成学习/面试准备问答。
    """
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if resume.status != ResumeStatus.OPTIMIZED:
        raise HTTPException(
            status_code=400,
            detail="仅「已完成优化」的任务可生成学习问答",
        )

    has_body = bool((resume.optimized_resume or "").strip())
    has_job = bool((resume.job_description or "").strip())
    has_ma = bool((resume.match_analysis or "").strip())
    if not has_body and not has_job and not has_ma:
        raise HTTPException(
            status_code=400,
            detail="缺少优化稿与岗位信息，无法生成学习问答",
        )

    ma_dict = None
    if resume.match_analysis:
        try:
            ma_dict = json.loads(resume.match_analysis)
        except json.JSONDecodeError:
            ma_dict = None

    max_items = max(1, min(settings.RESUME_STUDY_QA_MAX_ITEMS, 20))

    try:
        items = await generate_resume_study_qa(
            target_job_title=resume.target_job_title,
            job_description=resume.job_description,
            match_analysis=ma_dict if isinstance(ma_dict, dict) else None,
            optimized_resume=resume.optimized_resume or "",
            max_items=max_items,
        )
    except ValueError as e:
        logger.warning("study_qa generation failed: %s", e)
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        logger.exception("study_qa LLM error")
        raise HTTPException(
            status_code=502,
            detail="生成学习问答失败，请稍后重试",
        ) from e

    return SuccessResponse(
        success=True,
        message="学习问答已生成",
        data={
            "items": [i.model_dump() for i in items],
        },
    )


@router.get("/{resume_id}", response_model=SuccessResponse)
async def get_resume(
    resume_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    获取简历详情
    """
    logger.info(f"获取简历详情，ID: {resume_id}")
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    
    if not resume:
        logger.warning(f"简历不存在，ID: {resume_id}")
        raise HTTPException(status_code=404, detail="Resume not found")
    
    logger.debug(f"获取简历详情成功，ID: {resume_id}")
    return SuccessResponse(
        success=True,
        message="Resume retrieved successfully",
        data={
            "id": resume.id,
            "original_filename": resume.original_filename,
            "file_type": resume.file_type,
            "status": resume.status.value,
            "target_job_url": resume.target_job_url,
            "target_job_title": resume.target_job_title,
            "original_text": resume.original_text,
            "extracted_info": json.loads(resume.extracted_info) if resume.extracted_info else None,
            "match_analysis": json.loads(resume.match_analysis) if resume.match_analysis else None,
            "optimized_resume": resume.optimized_resume,
            "job_description": resume.job_description,
            "job_snapshot": json.loads(resume.job_snapshot) if resume.job_snapshot else None,
            "error_message": resume.error_message,
            "created_at": resume.created_at.isoformat(),
            "updated_at": resume.updated_at.isoformat(),
        },
    )


@router.get("/{resume_id}/download")
async def download_optimized_resume(
    resume_id: int,
    format: str = "md",
    db: AsyncSession = Depends(get_db),
):
    """
    下载优化后的简历
    
    支持 Markdown (md) 格式。PDF 格式需要额外处理。
    """
    logger.info(f"下载优化后的简历，ID: {resume_id}, 格式: {format}")
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    
    if not resume:
        logger.warning(f"简历不存在，ID: {resume_id}")
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if not resume.optimized_resume:
        logger.warning(f"简历未优化，ID: {resume_id}")
        raise HTTPException(
            status_code=400,
            detail="Resume has not been optimized yet",
        )
    
    if format.lower() == "md":
        # 返回 Markdown 文件
        filename = f"optimized_resume_{resume_id}.md"
        logger.debug(f"生成 Markdown 文件: {filename}")
        return Response(
            content=resume.optimized_resume,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )
    else:
        logger.warning(f"不支持的格式: {format}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Supported: md",
        )


@router.get("", response_model=SuccessResponse)
async def list_resumes(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    获取简历列表
    """
    logger.info(f"获取简历列表，跳过: {skip}, 限制: {limit}")
    user = await get_or_create_user(db)

    count_result = await db.execute(
        select(func.count()).select_from(Resume).where(Resume.user_id == user.id)
    )
    total = int(count_result.scalar_one() or 0)

    result = await db.execute(
        select(Resume)
        .where(Resume.user_id == user.id)
        .order_by(Resume.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    resumes = result.scalars().all()

    logger.debug(f"获取简历列表成功，数量: {len(resumes)}")
    return SuccessResponse(
        success=True,
        message="Resumes retrieved successfully",
        data={
            "resumes": [
                {
                    "id": r.id,
                    "original_filename": r.original_filename,
                    "file_type": r.file_type,
                    "status": r.status.value,
                    "target_job_title": r.target_job_title,
                    "target_job_url": r.target_job_url,
                    "error_message": r.error_message,
                    "created_at": r.created_at.isoformat(),
                    "updated_at": r.updated_at.isoformat(),
                }
                for r in resumes
            ],
            "total": total,
            "skip": skip,
            "limit": limit,
        },
    )


@router.delete("/{resume_id}", response_model=SuccessResponse)
async def delete_resume(
    resume_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    删除简历
    """
    logger.info(f"删除简历，ID: {resume_id}")
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    
    if not resume:
        logger.warning(f"简历不存在，ID: {resume_id}")
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # 删除文件
    try:
        file_path = Path(resume.file_path)
        if file_path.exists():
            file_path.unlink()
            logger.debug(f"删除文件成功: {file_path}")
    except Exception as e:
        logger.warning(f"删除文件失败: {str(e)}", exc_info=True)
    
    # 删除数据库记录
    await db.delete(resume)
    await db.commit()
    
    logger.info(f"删除简历成功，ID: {resume_id}")
    return SuccessResponse(
        success=True,
        message="Resume deleted successfully",
        data={"id": resume_id},
    )
