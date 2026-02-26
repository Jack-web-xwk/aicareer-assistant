"""
Interview API - 面试模拟接口

提供面试模拟功能，包括 WebSocket 实时语音交互。
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.interview import InterviewRecord, InterviewStatus
from app.models.user import User
from app.models.schemas import (
    InterviewStartRequest,
    InterviewResponse,
    InterviewReportResponse,
    SuccessResponse,
)
from app.agents.interview_agent import InterviewAgent, InterviewState

router = APIRouter()

# 存储活跃的面试会话（生产环境应使用 Redis）
active_sessions: Dict[str, InterviewState] = {}


async def get_or_create_user(db: AsyncSession, email: str = "default@example.com") -> User:
    """获取或创建默认用户"""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(email=email, username="Default User")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return user


@router.post("/start", response_model=SuccessResponse)
async def start_interview(
    request: InterviewStartRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    开始面试
    
    创建面试会话，初始化面试官，返回第一个问题。
    """
    try:
        # 获取用户
        user = await get_or_create_user(db)
        
        # 创建会话 ID
        session_id = str(uuid.uuid4())
        
        # 创建面试智能体
        agent = InterviewAgent()
        
        # 初始化面试
        state = await agent.start_interview(
            job_role=request.job_role,
            tech_stack=request.tech_stack,
            difficulty_level=request.difficulty_level,
            max_questions=settings.MAX_INTERVIEW_QUESTIONS,
        )
        
        # 存储会话状态
        active_sessions[session_id] = state
        
        # 创建数据库记录
        record = InterviewRecord(
            session_id=session_id,
            user_id=user.id,
            job_role=request.job_role,
            tech_stack=json.dumps(request.tech_stack, ensure_ascii=False),
            difficulty_level=request.difficulty_level,
            conversation_history=json.dumps(
                state.get("conversation_history", []),
                ensure_ascii=False,
            ),
            question_count=state.get("question_count", 1),
            status=InterviewStatus.IN_PROGRESS,
        )
        
        db.add(record)
        await db.commit()
        await db.refresh(record)
        
        return SuccessResponse(
            success=True,
            message="Interview started successfully",
            data={
                "session_id": session_id,
                "job_role": request.job_role,
                "tech_stack": request.tech_stack,
                "difficulty_level": request.difficulty_level,
                "current_question": state.get("current_question"),
                "question_number": state.get("question_count", 1),
                "total_questions": settings.MAX_INTERVIEW_QUESTIONS,
                "audio_base64": state.get("audio_output"),
            },
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start interview: {str(e)}",
        )


@router.post("/{session_id}/answer", response_model=SuccessResponse)
async def submit_answer(
    session_id: str,
    text_answer: Optional[str] = None,
    audio_base64: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    提交面试回答（REST API 方式）
    
    支持文本或音频输入。
    """
    # 获取会话状态
    state = active_sessions.get(session_id)
    
    if not state:
        # 尝试从数据库恢复
        result = await db.execute(
            select(InterviewRecord).where(InterviewRecord.session_id == session_id)
        )
        record = result.scalar_one_or_none()
        
        if not record:
            raise HTTPException(status_code=404, detail="Interview session not found")
        
        if record.status != InterviewStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail="Interview has already ended")
        
        # 恢复状态（简化处理）
        raise HTTPException(
            status_code=400,
            detail="Session expired. Please start a new interview.",
        )
    
    if not text_answer and not audio_base64:
        raise HTTPException(
            status_code=400,
            detail="Either text_answer or audio_base64 is required",
        )
    
    try:
        # 创建智能体
        agent = InterviewAgent()
        
        # 处理回答
        new_state = await agent.process_answer(
            state=state,
            audio_input=audio_base64,
            text_input=text_answer,
        )
        
        # 更新会话状态
        active_sessions[session_id] = new_state
        
        # 更新数据库记录
        result = await db.execute(
            select(InterviewRecord).where(InterviewRecord.session_id == session_id)
        )
        record = result.scalar_one_or_none()
        
        if record:
            record.conversation_history = json.dumps(
                new_state.get("conversation_history", []),
                ensure_ascii=False,
            )
            record.question_count = new_state.get("question_count", 0)
            
            if new_state.get("is_finished"):
                record.status = InterviewStatus.COMPLETED
                record.ended_at = datetime.utcnow()
                record.total_score = new_state.get("total_score")
                
                report = new_state.get("report", {})
                record.strengths = json.dumps(
                    report.get("strengths", []),
                    ensure_ascii=False,
                )
                record.weaknesses = json.dumps(
                    report.get("weaknesses", []),
                    ensure_ascii=False,
                )
                record.suggestions = json.dumps(
                    report.get("suggestions", []),
                    ensure_ascii=False,
                )
                record.detailed_report = report.get("detailed_report", "")
            
            await db.commit()
        
        return SuccessResponse(
            success=True,
            message="Answer processed successfully",
            data={
                "session_id": session_id,
                "is_finished": new_state.get("is_finished", False),
                "current_question": new_state.get("current_question"),
                "question_number": new_state.get("question_count", 0),
                "total_questions": new_state.get("max_questions", 5),
                "audio_base64": new_state.get("audio_output"),
                "transcript": new_state.get("current_answer"),
                "report": new_state.get("report") if new_state.get("is_finished") else None,
            },
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process answer: {str(e)}",
        )


@router.get("/{session_id}", response_model=SuccessResponse)
async def get_interview_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    获取面试状态
    """
    result = await db.execute(
        select(InterviewRecord).where(InterviewRecord.session_id == session_id)
    )
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # 获取内存中的状态
    state = active_sessions.get(session_id, {})
    
    return SuccessResponse(
        success=True,
        message="Interview status retrieved successfully",
        data={
            "session_id": session_id,
            "job_role": record.job_role,
            "tech_stack": json.loads(record.tech_stack),
            "status": record.status.value,
            "question_count": record.question_count,
            "total_questions": settings.MAX_INTERVIEW_QUESTIONS,
            "current_question": state.get("current_question"),
            "is_finished": record.status == InterviewStatus.COMPLETED,
            "started_at": record.started_at.isoformat(),
            "ended_at": record.ended_at.isoformat() if record.ended_at else None,
        },
    )


@router.get("/{session_id}/report", response_model=SuccessResponse)
async def get_interview_report(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    获取面试评估报告
    """
    result = await db.execute(
        select(InterviewRecord).where(InterviewRecord.session_id == session_id)
    )
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    if record.status != InterviewStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Interview has not completed yet",
        )
    
    return SuccessResponse(
        success=True,
        message="Interview report retrieved successfully",
        data={
            "session_id": session_id,
            "job_role": record.job_role,
            "tech_stack": json.loads(record.tech_stack),
            "total_score": record.total_score,
            "strengths": json.loads(record.strengths) if record.strengths else [],
            "weaknesses": json.loads(record.weaknesses) if record.weaknesses else [],
            "suggestions": json.loads(record.suggestions) if record.suggestions else [],
            "detailed_report": record.detailed_report,
            "duration_minutes": record.duration_minutes,
            "conversation_history": json.loads(record.conversation_history) if record.conversation_history else [],
            "completed_at": record.ended_at.isoformat() if record.ended_at else None,
        },
    )


@router.post("/{session_id}/end", response_model=SuccessResponse)
async def end_interview(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    提前结束面试
    """
    result = await db.execute(
        select(InterviewRecord).where(InterviewRecord.session_id == session_id)
    )
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    if record.status != InterviewStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Interview is not in progress")
    
    # 获取会话状态
    state = active_sessions.get(session_id)
    
    if state:
        # 生成报告
        agent = InterviewAgent()
        state["is_finished"] = True
        final_state = await agent._generate_report(state)
        
        # 更新数据库
        report = final_state.get("report", {})
        record.status = InterviewStatus.COMPLETED
        record.ended_at = datetime.utcnow()
        record.total_score = final_state.get("total_score")
        record.strengths = json.dumps(report.get("strengths", []), ensure_ascii=False)
        record.weaknesses = json.dumps(report.get("weaknesses", []), ensure_ascii=False)
        record.suggestions = json.dumps(report.get("suggestions", []), ensure_ascii=False)
        record.detailed_report = report.get("detailed_report", "")
        
        # 清理会话
        del active_sessions[session_id]
    else:
        record.status = InterviewStatus.CANCELLED
        record.ended_at = datetime.utcnow()
    
    await db.commit()
    
    return SuccessResponse(
        success=True,
        message="Interview ended successfully",
        data={
            "session_id": session_id,
            "status": record.status.value,
        },
    )


@router.websocket("/ws/{session_id}")
async def interview_websocket(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket 实时面试交互
    
    消息格式：
    - 客户端发送: {"type": "audio", "audio_base64": "..."} 或 {"type": "text", "content": "..."}
    - 服务器响应: {"type": "response", "question": "...", "audio_base64": "...", "is_finished": false}
    """
    await websocket.accept()
    
    # 检查会话是否存在
    state = active_sessions.get(session_id)
    
    if not state:
        await websocket.send_json({
            "type": "error",
            "message": "Session not found. Please start a new interview.",
        })
        await websocket.close()
        return
    
    try:
        # 发送当前状态
        await websocket.send_json({
            "type": "init",
            "session_id": session_id,
            "job_role": state.get("job_role"),
            "current_question": state.get("current_question"),
            "question_number": state.get("question_count", 1),
            "audio_base64": state.get("audio_output"),
        })
        
        # 创建智能体
        agent = InterviewAgent()
        
        while True:
            # 接收消息
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "audio":
                # 处理音频输入
                audio_base64 = data.get("audio_base64")
                new_state = await agent.process_answer(
                    state=state,
                    audio_input=audio_base64,
                )
            elif msg_type == "text":
                # 处理文本输入
                text_content = data.get("content")
                new_state = await agent.process_answer(
                    state=state,
                    text_input=text_content,
                )
            elif msg_type == "end":
                # 提前结束
                state["is_finished"] = True
                new_state = await agent._generate_report(state)
                new_state["is_finished"] = True
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                })
                continue
            
            # 更新会话状态
            state = new_state
            active_sessions[session_id] = state
            
            # 发送响应
            response = {
                "type": "response",
                "session_id": session_id,
                "current_question": state.get("current_question"),
                "question_number": state.get("question_count", 0),
                "audio_base64": state.get("audio_output"),
                "transcript": state.get("current_answer"),
                "is_finished": state.get("is_finished", False),
            }
            
            if state.get("is_finished"):
                response["report"] = state.get("report")
                # 清理会话
                if session_id in active_sessions:
                    del active_sessions[session_id]
            
            await websocket.send_json(response)
            
            if state.get("is_finished"):
                break
    
    except WebSocketDisconnect:
        # 客户端断开连接
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e),
        })
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@router.get("", response_model=SuccessResponse)
async def list_interviews(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    获取面试记录列表
    """
    user = await get_or_create_user(db)
    
    result = await db.execute(
        select(InterviewRecord)
        .where(InterviewRecord.user_id == user.id)
        .order_by(InterviewRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    records = result.scalars().all()
    
    return SuccessResponse(
        success=True,
        message="Interviews retrieved successfully",
        data={
            "interviews": [
                {
                    "session_id": r.session_id,
                    "job_role": r.job_role,
                    "tech_stack": json.loads(r.tech_stack),
                    "status": r.status.value,
                    "total_score": r.total_score,
                    "duration_minutes": r.duration_minutes,
                    "started_at": r.started_at.isoformat(),
                    "ended_at": r.ended_at.isoformat() if r.ended_at else None,
                }
                for r in records
            ],
            "total": len(records),
            "skip": skip,
            "limit": limit,
        },
    )
