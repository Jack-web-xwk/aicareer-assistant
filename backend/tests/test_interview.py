"""
面试模块测试

测试 /api/interview 路由下的核心接口：
- GET /api/interview - 面试记录列表
- POST /api/interview/start - 开始面试
- GET /api/interview/history - 历史记录

注意：部分测试可能因为 LLM 调用而失败，使用 mock 来避免实际调用。
"""

import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.database import Base, get_db
from app.core.auth import hash_password, create_access_token
from app.models.user import User
from app.models.interview import InterviewRecord, InterviewStatus


# 测试用内存数据库 URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环（session 级别）"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """
    创建测试数据库会话

    每个测试函数使用独立的内存数据库。
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession):
    """
    创建测试客户端
    """
    from main import app

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(test_db: AsyncSession):
    """
    创建测试用户
    """
    user = User(
        email="interviewuser@example.com",
        username="interviewuser",
        hashed_password=hash_password("password123"),
        phone="13800138000",
        is_active=True,
        is_verified=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def auth_headers(test_user: User):
    """
    创建认证请求头
    """
    token = create_access_token({"sub": test_user.id})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def sample_interview(test_db: AsyncSession, test_user: User):
    """
    创建示例面试记录
    """
    record = InterviewRecord(
        session_id="test-session-001",
        user_id=test_user.id,
        job_role="Python后端工程师",
        tech_stack=json.dumps(["Python", "FastAPI", "MySQL"]),
        difficulty_level="medium",
        conversation_history=json.dumps([]),
        question_count=0,
        status=InterviewStatus.IN_PROGRESS,
    )
    test_db.add(record)
    await test_db.commit()
    await test_db.refresh(record)
    return record


@pytest_asyncio.fixture(scope="function")
async def completed_interview(test_db: AsyncSession, test_user: User):
    """
    创建已完成的面试记录
    """
    from datetime import datetime, timedelta
    record = InterviewRecord(
        session_id="completed-session-001",
        user_id=test_user.id,
        job_role="Python后端工程师",
        tech_stack=json.dumps(["Python", "FastAPI", "MySQL"]),
        difficulty_level="medium",
        conversation_history=json.dumps([
            {"role": "assistant", "content": "请介绍一下 FastAPI"},
            {"role": "user", "content": "FastAPI 是一个现代的 Python Web 框架"},
        ]),
        question_count=5,
        total_score=85.0,
        strengths=json.dumps(["技术基础扎实", "表达清晰"]),
        weaknesses=json.dumps(["系统设计经验不足"]),
        suggestions=json.dumps(["多学习分布式系统设计"]),
        detailed_report="面试表现良好，技术基础扎实...",
        status=InterviewStatus.COMPLETED,
        started_at=datetime.utcnow() - timedelta(minutes=15),
        ended_at=datetime.utcnow(),
    )
    test_db.add(record)
    await test_db.commit()
    await test_db.refresh(record)
    return record


# ==================== 面试列表接口测试 ====================


@pytest.mark.asyncio
async def test_list_interviews_empty(client: AsyncClient, auth_headers: dict):
    """测试获取空面试列表"""
    response = await client.get("/api/interview", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["interviews"] == []
    assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_interviews_with_data(client: AsyncClient, auth_headers: dict, sample_interview: InterviewRecord):
    """测试获取有数据的面试列表"""
    response = await client.get("/api/interview", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["interviews"]) >= 1


@pytest.mark.asyncio
async def test_list_interviews_without_auth(client: AsyncClient):
    """测试未认证时获取面试列表返回 401"""
    response = await client.get("/api/interview")
    assert response.status_code == 401


# ==================== 开始面试接口测试 ====================


@pytest.mark.asyncio
async def test_start_interview_success(client: AsyncClient, auth_headers: dict):
    """测试开始面试成功（mock LLM 调用）"""
    # Mock InterviewAgent 的 start_interview 方法
    mock_state = {
        "job_role": "Python后端工程师",
        "tech_stack": ["Python", "FastAPI"],
        "difficulty_level": "medium",
        "current_question": "请介绍一下 FastAPI 的特点",
        "question_count": 1,
        "conversation_history": [],
        "audio_output": None,
    }

    with patch("app.api.interview.InterviewAgent") as MockAgent:
        mock_instance = MagicMock()
        mock_instance.start_interview = AsyncMock(return_value=mock_state)
        MockAgent.return_value = mock_instance

        response = await client.post(
            "/api/interview/start",
            headers=auth_headers,
            json={
                "job_role": "Python后端工程师",
                "tech_stack": ["Python", "FastAPI"],
                "difficulty_level": "medium",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "session_id" in data["data"]
    assert data["data"]["job_role"] == "Python后端工程师"
    assert data["data"]["current_question"] is not None


@pytest.mark.asyncio
async def test_start_interview_without_auth(client: AsyncClient):
    """测试未认证时开始面试返回 401"""
    response = await client.post(
        "/api/interview/start",
        json={
            "job_role": "Python后端工程师",
            "tech_stack": ["Python"],
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_start_interview_invalid_request(client: AsyncClient, auth_headers: dict):
    """测试开始面试请求参数无效"""
    response = await client.post(
        "/api/interview/start",
        headers=auth_headers,
        json={
            "job_role": "",  # 空岗位
            "tech_stack": [],  # 空技术栈
        },
    )
    # 验证失败或服务器错误
    assert response.status_code in [400, 422, 500]


# ==================== 面试状态接口测试 ====================


@pytest.mark.asyncio
async def test_get_interview_status(client: AsyncClient, auth_headers: dict, sample_interview: InterviewRecord):
    """测试获取面试状态"""
    response = await client.get(
        f"/api/interview/{sample_interview.session_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["session_id"] == sample_interview.session_id
    assert data["data"]["status"] == "in_progress"


@pytest.mark.asyncio
async def test_get_interview_status_not_found(client: AsyncClient, auth_headers: dict):
    """测试获取不存在的面试状态"""
    response = await client.get(
        "/api/interview/nonexistent-session-id",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ==================== 面试历史记录接口测试 ====================


@pytest.mark.asyncio
async def test_list_interview_history_empty(client: AsyncClient, auth_headers: dict):
    """测试获取空历史记录"""
    response = await client.get("/api/interview/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["items"] == []
    assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_interview_history_with_completed(client: AsyncClient, auth_headers: dict, completed_interview: InterviewRecord):
    """测试获取已完成面试的历史记录"""
    response = await client.get("/api/interview/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["items"]) >= 1
    assert data["data"]["items"][0]["job_role"] == "Python后端工程师"
    assert data["data"]["items"][0]["total_score"] == 85.0


@pytest.mark.asyncio
async def test_list_interview_history_excludes_in_progress(client: AsyncClient, auth_headers: dict, sample_interview: InterviewRecord):
    """测试历史记录不包含进行中的面试"""
    response = await client.get("/api/interview/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # 进行中的面试不应该出现在历史记录中
    session_ids = [item["session_id"] for item in data["data"]["items"]]
    assert sample_interview.session_id not in session_ids


@pytest.mark.asyncio
async def test_list_interview_history_without_auth(client: AsyncClient):
    """测试未认证时获取历史记录返回 401"""
    response = await client.get("/api/interview/history")
    assert response.status_code == 401


# ==================== 面试报告接口测试 ====================


@pytest.mark.asyncio
async def test_get_interview_report(client: AsyncClient, auth_headers: dict, completed_interview: InterviewRecord):
    """测试获取已完成面试的评估报告"""
    response = await client.get(
        f"/api/interview/{completed_interview.session_id}/report",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total_score"] == 85.0
    assert len(data["data"]["strengths"]) >= 1


@pytest.mark.asyncio
async def test_get_interview_report_not_completed(client: AsyncClient, auth_headers: dict, sample_interview: InterviewRecord):
    """测试获取未完成面试的报告"""
    response = await client.get(
        f"/api/interview/{sample_interview.session_id}/report",
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "not completed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_interview_report_not_found(client: AsyncClient, auth_headers: dict):
    """测试获取不存在面试的报告"""
    response = await client.get(
        "/api/interview/nonexistent-session/report",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ==================== 结束面试接口测试 ====================


@pytest.mark.asyncio
async def test_end_interview_success(client: AsyncClient, auth_headers: dict, sample_interview: InterviewRecord):
    """测试提前结束面试"""
    with patch("app.api.interview.InterviewAgent") as MockAgent:
        mock_instance = MagicMock()
        mock_instance._generate_report = AsyncMock(return_value={
            "is_finished": True,
            "total_score": 70.0,
            "report": {
                "strengths": ["基础扎实"],
                "weaknesses": ["经验不足"],
                "suggestions": ["多学习"],
                "detailed_report": "面试报告...",
            },
        })
        MockAgent.return_value = mock_instance

        response = await client.post(
            f"/api/interview/{sample_interview.session_id}/end",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_end_interview_already_completed(client: AsyncClient, auth_headers: dict, completed_interview: InterviewRecord):
    """测试结束已完成的面试"""
    response = await client.post(
        f"/api/interview/{completed_interview.session_id}/end",
        headers=auth_headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_end_interview_not_found(client: AsyncClient, auth_headers: dict):
    """测试结束不存在的面试"""
    response = await client.post(
        "/api/interview/nonexistent-session/end",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ==================== 综合测试 ====================


@pytest.mark.asyncio
async def test_interview_flow(client: AsyncClient, auth_headers: dict):
    """测试面试完整流程：开始 -> 查看状态 -> 查看历史"""
    # Mock InterviewAgent
    mock_state = {
        "job_role": "Python后端工程师",
        "tech_stack": ["Python", "FastAPI"],
        "difficulty_level": "medium",
        "current_question": "请介绍一下 FastAPI 的特点",
        "question_count": 1,
        "conversation_history": [],
        "audio_output": None,
    }

    with patch("app.api.interview.InterviewAgent") as MockAgent:
        mock_instance = MagicMock()
        mock_instance.start_interview = AsyncMock(return_value=mock_state)
        MockAgent.return_value = mock_instance

        # 1. 开始面试
        start_response = await client.post(
            "/api/interview/start",
            headers=auth_headers,
            json={
                "job_role": "Python后端工程师",
                "tech_stack": ["Python", "FastAPI"],
            },
        )
        assert start_response.status_code == 200
        session_id = start_response.json()["data"]["session_id"]

    # 2. 查看状态
    status_response = await client.get(
        f"/api/interview/{session_id}",
        headers=auth_headers,
    )
    assert status_response.status_code == 200
    assert status_response.json()["data"]["status"] == "in_progress"

    # 3. 列表中应该能看到
    list_response = await client.get("/api/interview", headers=auth_headers)
    assert list_response.status_code == 200
    session_ids = [i["session_id"] for i in list_response.json()["data"]["interviews"]]
    assert session_id in session_ids


@pytest.mark.asyncio
async def test_interview_history_pagination(client: AsyncClient, auth_headers: dict, test_db: AsyncSession, test_user: User):
    """测试历史记录分页"""
    from datetime import datetime, timedelta

    # 创建多条已完成的面试记录
    for i in range(5):
        record = InterviewRecord(
            session_id=f"history-session-{i:03d}",
            user_id=test_user.id,
            job_role=f"岗位{i}",
            tech_stack=json.dumps(["Python"]),
            difficulty_level="medium",
            conversation_history=json.dumps([]),
            question_count=5,
            total_score=float(70 + i * 5),
            status=InterviewStatus.COMPLETED,
            started_at=datetime.utcnow() - timedelta(hours=i),
            ended_at=datetime.utcnow() - timedelta(hours=i - 1),
        )
        test_db.add(record)
    await test_db.commit()

    # 测试分页
    response = await client.get(
        "/api/interview/history?skip=0&limit=3",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["items"]) == 3
    assert data["data"]["total"] == 5

    # 第二页
    response2 = await client.get(
        "/api/interview/history?skip=3&limit=3",
        headers=auth_headers,
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["data"]["items"]) == 2
