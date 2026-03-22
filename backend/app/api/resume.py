"""
Resume API - 简历相关接口

提供简历上传、解析、优化和下载功能。
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import FileProcessingException, NotFoundException
from app.models.resume import Resume, ResumeStatus
from app.models.user import User
from app.models.schemas import (
    ResumeResponse,
    OptimizedResumeResponse,
    SuccessResponse,
    ErrorResponse,
    ExtractedResumeInfo,
    JobRequirements,
    MatchAnalysis,
)
from app.services.resume_parser import parse_resume_file
from app.services.job_scraper import scrape_job_info
from app.agents.resume_optimizer_agent import ResumeOptimizerAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _job_desc_text_from_requirements(job_info: JobRequirements, job_url: str) -> str:
    """将爬取结果格式化为给 LLM 的岗位说明文本。"""
    lines = [
        f"岗位名称：{job_info.title}",
        f"公司：{job_info.company or '未知'}",
        f"应聘岗位链接：{job_url}",
        f"薪资：{job_info.salary or '未标注'}",
        f"工作地点：{job_info.location or '未标注'}",
    ]
    if job_info.industry:
        lines.append(f"行业：{job_info.industry}")
    if job_info.company_scale:
        lines.append(f"公司规模：{job_info.company_scale}")
    if job_info.financing_stage:
        lines.append(f"融资阶段：{job_info.financing_stage}")
    lines.append("职责：")
    lines.extend("- " + r for r in job_info.responsibilities)
    lines.append("必备技能：")
    lines.extend("- " + s for s in job_info.required_skills)
    lines.append("加分技能：")
    lines.extend("- " + s for s in job_info.preferred_skills)
    lines.append(f"经验要求：{job_info.experience_years or '未指定'}")
    lines.append(f"学历要求：{job_info.education_requirement or '未指定'}")
    return "\n".join(lines)


def _job_snapshot_json(job_info: JobRequirements, job_url: str) -> str:
    """结构化快照，供历史结果展示。"""
    d = job_info.model_dump()
    d["source_url"] = job_url
    return json.dumps(d, ensure_ascii=False)


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


@router.post("/optimize/{resume_id}", response_model=SuccessResponse)
async def optimize_resume(
    resume_id: int,
    target_job_url: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """
    优化简历
    
    基于目标岗位需求优化简历内容。
    """
    logger.info(f"开始优化简历，ID: {resume_id}")
    
    # 获取简历记录
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    
    if not resume:
        logger.warning(f"简历不存在，ID: {resume_id}")
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # 使用新的目标岗位链接或已有的
    job_url = target_job_url or resume.target_job_url
    
    if not job_url:
        logger.warning(f"目标岗位 URL 缺失，ID: {resume_id}")
        raise HTTPException(
            status_code=400,
            detail="Target job URL is required for optimization",
        )
    
    # 检查简历是否已解析
    if not resume.original_text:
        logger.warning(f"简历未解析，ID: {resume_id}")
        raise HTTPException(
            status_code=400,
            detail="Resume has not been parsed. Please re-upload.",
        )
    
    try:
        # 更新状态
        resume.status = ResumeStatus.OPTIMIZING
        resume.target_job_url = job_url
        await db.commit()
        logger.debug(f"更新简历状态为 OPTIMIZING，ID: {resume_id}")
        
        # 爬取岗位信息
        try:
            logger.info(f"开始爬取岗位信息: {job_url}")
            job_info = scrape_job_info(job_url)
            job_desc = _job_desc_text_from_requirements(job_info, job_url)
            resume.target_job_title = job_info.title
            resume.job_description = job_desc
            resume.job_snapshot = _job_snapshot_json(job_info, job_url)
            logger.info(f"岗位信息爬取成功: {job_info.title}")
        except Exception as e:
            # 如果爬取失败，使用 URL 作为描述
            logger.error(f"岗位信息爬取失败: {str(e)}", exc_info=True)
            job_desc = f"目标岗位链接：{job_url}"
            resume.job_description = job_desc
            resume.job_snapshot = json.dumps(
                {"source_url": job_url, "scrape_error": str(e)},
                ensure_ascii=False,
            )
        
        # 运行简历优化智能体
        logger.info("开始运行简历优化智能体")
        agent = ResumeOptimizerAgent()
        result_state = await agent.run(
            resume_text=resume.original_text,
            job_desc=job_desc,
            job_url=job_url,
        )
        logger.debug("简历优化智能体运行完成")
        
        # 保存结果
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
            logger.info("简历优化成功")
        
        await db.commit()
        await db.refresh(resume)
        
        return SuccessResponse(
            success=True,
            message="Resume optimized successfully",
            data={
                "id": resume.id,
                "status": resume.status.value,
                "target_job_title": resume.target_job_title,
                "optimized_resume": resume.optimized_resume,
                "match_analysis": json.loads(resume.match_analysis) if resume.match_analysis else None,
                "updated_at": resume.updated_at.isoformat(),
            },
        )
    
    except Exception as e:
        logger.error(f"优化简历失败: {str(e)}", exc_info=True)
        resume.status = ResumeStatus.FAILED
        resume.error_message = str(e)
        await db.commit()
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to optimize resume: {str(e)}",
        )


@router.post("/optimize/{resume_id}/stream")
async def optimize_resume_stream(
    resume_id: int,
    target_job_url: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """流式优化简历（SSE）。"""
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

    resume.status = ResumeStatus.OPTIMIZING
    resume.target_job_url = job_url
    await db.commit()

    try:
        job_info = scrape_job_info(job_url)
        job_desc = _job_desc_text_from_requirements(job_info, job_url)
        resume.target_job_title = job_info.title
        resume.job_description = job_desc
        resume.job_snapshot = _job_snapshot_json(job_info, job_url)
    except Exception as e:
        logger.error(
            f"流式优化岗位信息爬取失败，resume_id={resume_id}, url={job_url}, error={str(e)}",
            exc_info=True,
        )
        job_desc = f"目标岗位链接：{job_url}"
        resume.job_description = job_desc
        resume.job_snapshot = json.dumps(
            {"source_url": job_url, "scrape_error": str(e)},
            ensure_ascii=False,
        )
    await db.commit()

    async def event_generator() -> AsyncGenerator[str, None]:
        agent = ResumeOptimizerAgent()
        final_extracted_info = None
        final_match_analysis = None
        final_optimized_resume = ""
        has_error = False

        try:
            async for event in agent.run_stream(
                resume_text=resume.original_text or "",
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
                    resume.status = ResumeStatus.FAILED
                    resume.error_message = event.get("message", "Unknown stream error")
                    await db.commit()
                    logger.error(
                        "流式简历优化失败: resume_id=%s, error=%s",
                        resume_id,
                        resume.error_message,
                    )

                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            if not has_error:
                resume.status = ResumeStatus.OPTIMIZED
                resume.extracted_info = json.dumps(final_extracted_info or {}, ensure_ascii=False)
                resume.match_analysis = json.dumps(final_match_analysis or {}, ensure_ascii=False)
                resume.optimized_resume = final_optimized_resume
                await db.commit()
                logger.info(f"流式简历优化完成，resume_id={resume_id}")
        except Exception as e:
            logger.error(
                f"流式简历优化异常，resume_id={resume_id}, error={str(e)}",
                exc_info=True,
            )
            resume.status = ResumeStatus.FAILED
            resume.error_message = str(e)
            await db.commit()
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
