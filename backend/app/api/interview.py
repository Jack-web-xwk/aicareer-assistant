"""
Interview API - 面试模拟接口

提供面试模拟功能，包括 WebSocket 实时语音交互和 SSE 流式返回。
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.redis_client import get_redis_client
from app.models.interview import InterviewRecord, InterviewStatus
from app.models.user import User
from app.models.schemas import (
    InterviewStartRequest,
    InterviewResponse,
    InterviewReportResponse,
    SuccessResponse,
)
from app.agents.interview_agent import InterviewAgent, InterviewState
from app.services.question_service import QuestionService
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Redis 客户端（用于会话持久化）
# 迁移计划：
# Day 1-2: Dual-write (同时写入内存和 Redis)
# Day 3: 验证数据一致性
# Day 4: 切换读操作到 Redis
# Day 5: 清理内存存储代码
active_sessions: Dict[str, InterviewState] = {}  # TODO: Phase out after migration

# WebSocket 连接管理：每个 session_id 最多允许 1 个连接
# 存储 session_id -> WebSocket 实例，用于替换旧连接
_active_ws_connections: Dict[str, WebSocket] = {}

# 心跳超时阈值（秒）：超过该时间无活动则断开
WS_HEARTBEAT_TIMEOUT = 60


async def get_session_from_redis(session_id: str) -> Optional[InterviewState]:
    """从 Redis 获取会话状态（带 fallback 逻辑）"""
    redis_client = get_redis_client()
    
    # 优先从 Redis 读取
    try:
        state = await redis_client.get_session(session_id)
        if state:
            logger.debug(f"从 Redis 恢复会话：{session_id}")
            return state
    except Exception as e:
        logger.warning(f"Redis 读取失败，回退到内存：{e}")
    
    # Fallback: 从内存读取
    return active_sessions.get(session_id)


async def save_session_to_redis(session_id: str, state: InterviewState):
    """保存会话状态到 Redis（dual-write）"""
    # Dual-write: 同时写入内存和 Redis
    active_sessions[session_id] = state
    
    try:
        redis_client = get_redis_client()
        await redis_client.save_session(session_id, state, ttl=604800)  # 7 days TTL
        logger.debug(f"Dual-write 会话到 Redis: {session_id}")
    except Exception as e:
        logger.error(f"Redis 写入失败，但内存写入成功：{e}")


async def delete_session_from_redis(session_id: str):
    """从 Redis 和内存中删除会话"""
    # 清理内存
    if session_id in active_sessions:
        del active_sessions[session_id]
    
    # 清理 Redis
    try:
        redis_client = get_redis_client()
        await redis_client.delete_session(session_id)
        logger.debug(f"从 Redis 删除会话：{session_id}")
    except Exception as e:
        logger.error(f"Redis 删除失败：{e}")


async def get_or_create_user(db: AsyncSession, current_user: User = Depends(get_current_user)) -> User:
    """获取当前已认证用户"""
    return current_user


@router.post("/start", response_model=SuccessResponse)
async def start_interview(
    request: InterviewStartRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    开始面试
    
    创建面试会话，初始化面试官，返回第一个问题。
    """
    logger.info(f"开始面试，岗位: {request.job_role}, 技术栈: {request.tech_stack}")
    try:
        # 获取用户
        user = await get_or_create_user(db)
        logger.debug(f"获取用户: {user.email}")
        
        # 创建会话 ID
        session_id = str(uuid.uuid4())
        logger.debug(f"创建会话 ID: {session_id}")
        
        # 创建题库服务（用于 hybrid mode）
        question_service = QuestionService(db)
        
        # 创建面试智能体（启用混合模式）
        agent = InterviewAgent(
            question_service=question_service,
            use_hybrid_mode=True,
        )
        
        # 初始化面试
        logger.info("初始化面试智能体")
        state = await agent.start_interview(
            job_role=request.job_role,
            tech_stack=request.tech_stack,
            difficulty_level=request.difficulty_level,
            max_questions=settings.MAX_INTERVIEW_QUESTIONS,
        )
        logger.debug("面试智能体初始化完成")
        
        # 存储会话状态（Dual-write: 内存 + Redis）
        await save_session_to_redis(session_id, state)
        
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
        
        logger.info(f"面试开始成功，会话 ID: {session_id}")
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
        logger.error(f"开始面试失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start interview: {str(e)}",
        )


@router.post("/{session_id}/answer/stream")
async def submit_answer_stream(
    session_id: str,
    text_answer: Optional[str] = None,
    audio_base64: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    提交面试回答（SSE 流式返回）
    
    支持文本或音频输入，返回 SSE 流式响应。
    """
    logger.info(f"提交面试回答（流式），会话 ID: {session_id}")
    
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # 获取会话状态（优先 Redis）
            state = await get_session_from_redis(session_id)
            
            if not state:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Session not found'}, ensure_ascii=False)}\n\n"
                return
            
            if not text_answer and not audio_base64:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Answer is required'}, ensure_ascii=False)}\n\n"
                return
            
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'message': 'Processing your answer...'}, ensure_ascii=False)}\n\n"
            
            # 创建智能体
            agent = InterviewAgent()
            
            # 发送处理中事件
            yield f"data: {json.dumps({'type': 'processing', 'message': 'Analyzing your response...'}, ensure_ascii=False)}\n\n"
            
            # 处理回答
            logger.info("处理面试回答")
            new_state = await agent.process_answer(
                state=state,
                audio_input=audio_base64,
                text_input=text_answer,
            )
            logger.debug("回答处理完成")
            
            # 更新会话状态（Dual-write: 内存 + Redis）
            await save_session_to_redis(session_id, new_state)
            
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
                    logger.info(f"面试完成，会话 ID: {session_id}")
                
                await db.commit()
            
            # 发送结果事件
            response_data = {
                "type": "response",
                "session_id": session_id,
                "is_finished": new_state.get("is_finished", False),
                "current_question": new_state.get("current_question"),
                "question_number": new_state.get("question_count", 0),
                "total_questions": new_state.get("max_questions", 5),
                "audio_base64": new_state.get("audio_output"),
                "transcript": new_state.get("current_answer"),
            }
            
            if new_state.get("is_finished"):
                response_data["report"] = new_state.get("report")
            
            yield f"data: {json.dumps(response_data, ensure_ascii=False)}\n\n"
            
            # 发送完成事件
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
            
            logger.info(f"回答处理成功，会话 ID: {session_id}")
        
        except Exception as e:
            logger.error(f"处理回答失败: {str(e)}", exc_info=True)
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


@router.post("/{session_id}/answer", response_model=SuccessResponse)
async def submit_answer(
    session_id: str,
    text_answer: Optional[str] = None,
    audio_base64: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    提交面试回答（REST API 方式 - 非流式）
    
    支持文本或音频输入。建议使用 /answer/stream 接口获得更好的实时体验。
    """
    logger.info(f"提交面试回答，会话 ID: {session_id}")
    # 获取会话状态（优先 Redis）
    state = await get_session_from_redis(session_id)
    
    if not state:
        # 尝试从数据库恢复
        logger.warning(f"会话状态不存在，尝试从数据库恢复: {session_id}")
        result = await db.execute(
            select(InterviewRecord).where(InterviewRecord.session_id == session_id)
        )
        record = result.scalar_one_or_none()
        
        if not record:
            logger.warning(f"面试会话不存在: {session_id}")
            raise HTTPException(status_code=404, detail="Interview session not found")
        
        if record.status != InterviewStatus.IN_PROGRESS:
            logger.warning(f"面试已结束: {session_id}")
            raise HTTPException(status_code=400, detail="Interview has already ended")
        
        # 恢复状态（简化处理）
        logger.warning(f"会话已过期: {session_id}")
        raise HTTPException(
            status_code=400,
            detail="Session expired. Please start a new interview.",
        )
    
    if not text_answer and not audio_base64:
        logger.warning(f"回答内容为空: {session_id}")
        raise HTTPException(
            status_code=400,
            detail="Either text_answer or audio_base64 is required",
        )
    
    try:
        # 创建智能体
        agent = InterviewAgent()
        
        # 处理回答
        logger.info("处理面试回答")
        new_state = await agent.process_answer(
            state=state,
            audio_input=audio_base64,
            text_input=text_answer,
        )
        logger.debug("回答处理完成")
        
        # 更新会话状态（Dual-write: 内存 + Redis）
        await save_session_to_redis(session_id, new_state)
        
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
                logger.info(f"面试完成，会话 ID: {session_id}")
            
            await db.commit()
        
        logger.info(f"回答处理成功，会话 ID: {session_id}")
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
        logger.error(f"处理回答失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process answer: {str(e)}",
        )


@router.get("/history", response_model=SuccessResponse)
async def list_interview_history(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    历史结果：仅返回当前用户已完成的模拟面试（含评估报告），按结束时间倒序。
    完整报告请用 GET /interview/{session_id}/report。
    """
    user = await get_or_create_user(db)

    count_result = await db.execute(
        select(func.count())
        .select_from(InterviewRecord)
        .where(
            InterviewRecord.user_id == user.id,
            InterviewRecord.status == InterviewStatus.COMPLETED,
        )
    )
    total = int(count_result.scalar_one() or 0)

    result = await db.execute(
        select(InterviewRecord)
        .where(
            InterviewRecord.user_id == user.id,
            InterviewRecord.status == InterviewStatus.COMPLETED,
        )
        .order_by(InterviewRecord.ended_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = result.scalars().all()

    items = []
    for r in rows:
        preview = ""
        if r.detailed_report:
            preview = (r.detailed_report or "")[:280].replace("\n", " ")
            if len(r.detailed_report or "") > 280:
                preview += "…"
        items.append(
            {
                "session_id": r.session_id,
                "job_role": r.job_role,
                "tech_stack": json.loads(r.tech_stack),
                "total_score": r.total_score,
                "duration_minutes": r.duration_minutes,
                "preview": preview or None,
                "started_at": r.started_at.isoformat(),
                "ended_at": r.ended_at.isoformat() if r.ended_at else None,
            }
        )

    return SuccessResponse(
        success=True,
        message="Interview history retrieved successfully",
        data={
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        },
    )


@router.get("/{session_id}", response_model=SuccessResponse)
async def get_interview_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    获取面试状态
    """
    logger.info(f"获取面试状态，会话 ID: {session_id}")
    result = await db.execute(
        select(InterviewRecord).where(InterviewRecord.session_id == session_id)
    )
    record = result.scalar_one_or_none()
    
    if not record:
        logger.warning(f"面试会话不存在: {session_id}")
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    # 获取内存中的状态（优先 Redis）
    state = await get_session_from_redis(session_id) or {}
    
    logger.debug(f"获取面试状态成功，会话 ID: {session_id}")
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
    logger.info(f"获取面试评估报告，会话 ID: {session_id}")
    result = await db.execute(
        select(InterviewRecord).where(InterviewRecord.session_id == session_id)
    )
    record = result.scalar_one_or_none()
    
    if not record:
        logger.warning(f"面试会话不存在: {session_id}")
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    if record.status != InterviewStatus.COMPLETED:
        logger.warning(f"面试未完成: {session_id}")
        raise HTTPException(
            status_code=400,
            detail="Interview has not completed yet",
        )
    
    logger.debug(f"获取面试评估报告成功，会话 ID: {session_id}")
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
    logger.info(f"提前结束面试，会话 ID: {session_id}")
    result = await db.execute(
        select(InterviewRecord).where(InterviewRecord.session_id == session_id)
    )
    record = result.scalar_one_or_none()
    
    if not record:
        logger.warning(f"面试会话不存在: {session_id}")
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    if record.status != InterviewStatus.IN_PROGRESS:
        logger.warning(f"面试不在进行中: {session_id}")
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
        logger.info(f"面试完成并清理会话，会话 ID: {session_id}")
    else:
        record.status = InterviewStatus.CANCELLED
        record.ended_at = datetime.utcnow()
        logger.info(f"面试取消，会话 ID: {session_id}")
    
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
    - 心跳: 客户端 {"type": "ping"} -> 服务端 {"type": "pong"}
    """
    logger.info(f"WebSocket 连接请求，会话 ID: {session_id}")

    # ========== 1. 连接数限制：同一个 session_id 最多 1 个连接 ==========
    # 检查是否已有活跃连接，如有则优雅断开旧连接
    old_ws = _active_ws_connections.get(session_id)
    if old_ws is not None:
        logger.info(f"会话 {session_id} 已有活跃连接，将替换旧连接")
        try:
            await old_ws.close(code=1012, reason="Replaced by new connection")
        except Exception:
            # 旧连接可能已经断开，忽略关闭异常
            pass
        finally:
            # 从连接注册表中移除旧连接
            _active_ws_connections.pop(session_id, None)

    # 接受新连接
    await websocket.accept()

    # 注册新连接
    _active_ws_connections[session_id] = websocket
    logger.info(f"WebSocket 连接已建立，会话 ID: {session_id}")

    # ========== 初始化会话状态 ==========
    state = active_sessions.get(session_id)

    if not state:
        logger.warning(f"会话不存在，WebSocket 连接失败: {session_id}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Session not found. Please start a new interview.",
            })
        except Exception:
            pass
        finally:
            await _cleanup_ws_connection(session_id, websocket)
        return

    # 发送当前状态
    try:
        await websocket.send_json({
            "type": "init",
            "session_id": session_id,
            "job_role": state.get("job_role"),
            "current_question": state.get("current_question"),
            "question_number": state.get("question_count", 1),
            "audio_base64": state.get("audio_output"),
        })
    except Exception as e:
        logger.error(f"发送初始化消息失败: {str(e)}")
        await _cleanup_ws_connection(session_id, websocket)
        return

    # 创建智能体
    agent = InterviewAgent()

    # ========== 2. 心跳检测：跟踪最后活动时间 ==========
    last_heartbeat = __import__("time").time()

    try:
        while True:
            # 使用超时接收消息，用于心跳检测
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=WS_HEARTBEAT_TIMEOUT,
                )
            except asyncio.TimeoutError:
                # 超过 WS_HEARTBEAT_TIMEOUT 秒无消息，判定为心跳超时
                logger.warning(f"心跳超时，自动断开连接: {session_id}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Heartbeat timeout. Connection closed.",
                })
                break

            # 更新最后活动时间
            last_heartbeat = __import__("time").time()
            msg_type = data.get("type")

            # ========== 心跳处理 ==========
            if msg_type == "ping":
                logger.debug(f"收到心跳 ping: {session_id}")
                try:
                    await websocket.send_json({"type": "pong"})
                except Exception:
                    break
                continue

            # ========== 业务消息处理 ==========
            if msg_type == "audio":
                # 处理音频输入
                audio_base64 = data.get("audio_base64")
                logger.debug("处理音频输入")
                new_state = await agent.process_answer(
                    state=state,
                    audio_input=audio_base64,
                )

            elif msg_type == "text":
                # 处理文本输入
                text_content = data.get("content")
                logger.debug("处理文本输入")
                new_state = await agent.process_answer(
                    state=state,
                    text_input=text_content,
                )

            elif msg_type == "end":
                # 提前结束
                logger.info("提前结束面试")
                state["is_finished"] = True
                new_state = await agent._generate_report(state)
                new_state["is_finished"] = True

            else:
                # 未知消息类型：返回错误但不崩溃，继续监听
                logger.warning(f"未知消息类型: {msg_type}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                })
                continue

            # 更新会话状态（Dual-write）
            state = new_state
            await save_session_to_redis(session_id, state)

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
                logger.info(f"面试完成，准备关闭 WebSocket: {session_id}")

            await websocket.send_json(response)

            if state.get("is_finished"):
                break

    except WebSocketDisconnect:
        # 客户端正常断开连接
        logger.info(f"WebSocket 客户端断开连接: {session_id}")

    except Exception as e:
        # 其他未知异常
        logger.error(f"WebSocket 错误: {str(e)}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Internal server error: {str(e)}",
            })
        except Exception:
            # 发送错误消息也失败，说明连接已不可用
            pass

    finally:
        # ========== 3. 内存清理：断开连接时清理所有关联状态 ==========
        await _cleanup_ws_connection(session_id, websocket)


async def _cleanup_ws_connection(session_id: str, websocket: WebSocket):
    """
    清理 WebSocket 连接关联的所有资源

    Args:
        session_id: 会话 ID
        websocket: WebSocket 实例
    """
    # 从连接注册表中移除（仅移除当前连接，避免误删替换后的新连接）
    current_ws = _active_ws_connections.get(session_id)
    if current_ws is websocket:
        _active_ws_connections.pop(session_id, None)
        logger.debug(f"已从连接注册表移除: {session_id}")

    # 关闭 WebSocket 连接
    try:
        await websocket.close(code=1000, reason="Normal closure")
    except Exception:
        # 连接可能已经关闭
        pass

    logger.info(f"WebSocket 连接已清理，会话 ID: {session_id}")


@router.get("", response_model=SuccessResponse)
async def list_interviews(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    获取面试记录列表
    """
    logger.info(f"获取面试记录列表，跳过: {skip}, 限制: {limit}")
    user = await get_or_create_user(db)
    
    result = await db.execute(
        select(InterviewRecord)
        .where(InterviewRecord.user_id == user.id)
        .order_by(InterviewRecord.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    records = result.scalars().all()
    
    logger.debug(f"获取面试记录列表成功，数量: {len(records)}")
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
