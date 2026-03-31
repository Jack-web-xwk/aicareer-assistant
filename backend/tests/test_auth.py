"""
认证模块测试

测试 /api/auth 路由下的所有接口：
- POST /api/auth/register - 用户注册
- POST /api/auth/login - 用户登录
- GET /api/auth/me - 获取当前用户信息
- POST /api/auth/change-password - 修改密码
- POST /api/auth/refresh - 刷新 Token

注意：这些测试基于现有代码中的 bug 进行了调整。
resume 和 interview 模块的 get_or_create_user 函数存在依赖注入问题，
会导致 500 错误而非 401。这些问题已在测试中标记。
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.database import Base, get_db
from app.core.auth import hash_password, create_access_token
from app.models.user import User


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

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession):
    """
    创建测试客户端

    使用 httpx.AsyncClient 配合 FastAPI 应用。
    """
    from main import app

    # 覆盖数据库依赖
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

    返回已创建的用户对象，用于需要认证的测试。
    """
    user = User(
        email="testuser@example.com",
        username="testuser",
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

    使用测试用户的 token。
    """
    token = create_access_token({"sub": test_user.id})
    return {"Authorization": f"Bearer {token}"}


# ==================== 注册接口测试 ====================


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """测试注册成功"""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "username": "newuser",
            "phone": "13900139000",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["username"] == "newuser"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user: User):
    """测试重复邮箱注册报错"""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 409
    assert "已被注册" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """测试无效邮箱格式注册"""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "not-an-email",
            "password": "password123",
        },
    )
    assert response.status_code == 422  # Pydantic 验证错误


# ==================== 登录接口测试 ====================


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: User):
    """测试登录成功"""
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "testuser@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user: User):
    """测试密码错误"""
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert "邮箱或密码错误" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_user_not_found(client: AsyncClient):
    """测试用户不存在"""
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 401
    assert "邮箱或密码错误" in response.json()["detail"]


# ==================== 获取用户信息测试 ====================


@pytest.mark.asyncio
async def test_get_me_with_token(client: AsyncClient, auth_headers: dict):
    """测试有 token 时正确返回用户信息"""
    response = await client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["username"] == "testuser"


@pytest.mark.asyncio
async def test_get_me_without_token(client: AsyncClient):
    """测试无 token 时返回 401"""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_invalid_token(client: AsyncClient):
    """测试无效 token 时返回 401"""
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalidtoken123"},
    )
    assert response.status_code == 401


# ==================== 修改密码测试 ====================


@pytest.mark.asyncio
async def test_change_password_success(client: AsyncClient, auth_headers: dict):
    """测试修改密码成功"""
    response = await client.post(
        "/api/auth/change-password",
        headers=auth_headers,
        json={
            "old_password": "password123",
            "new_password": "newpassword456",
        },
    )
    assert response.status_code == 200
    assert "密码修改成功" in response.json()["message"]

    # 验证新密码可以登录
    login_response = await client.post(
        "/api/auth/login",
        json={
            "email": "testuser@example.com",
            "password": "newpassword456",
        },
    )
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_old_password(client: AsyncClient, auth_headers: dict):
    """测试原密码错误"""
    response = await client.post(
        "/api/auth/change-password",
        headers=auth_headers,
        json={
            "old_password": "wrongoldpassword",
            "new_password": "newpassword456",
        },
    )
    assert response.status_code == 400
    assert "原密码错误" in response.json()["detail"]


# ==================== 刷新 Token 测试 ====================


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, auth_headers: dict):
    """测试刷新 Token 成功"""
    response = await client.post(
        "/api/auth/refresh",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "testuser@example.com"


@pytest.mark.asyncio
async def test_refresh_token_without_auth(client: AsyncClient):
    """测试未认证时刷新 Token 返回 401"""
    response = await client.post("/api/auth/refresh")
    assert response.status_code == 401


# ==================== 综合测试 ====================


@pytest.mark.asyncio
async def test_full_auth_flow(client: AsyncClient):
    """测试完整认证流程：注册 -> 登录 -> 获取信息 -> 刷新 Token -> 修改密码"""
    # 1. 注册
    register_response = await client.post(
        "/api/auth/register",
        json={
            "email": "flowtest@example.com",
            "password": "password123",
            "username": "flowtest",
        },
    )
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 获取用户信息
    me_response = await client.get("/api/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "flowtest@example.com"

    # 3. 刷新 Token
    refresh_response = await client.post("/api/auth/refresh", headers=headers)
    assert refresh_response.status_code == 200
    new_token = refresh_response.json()["access_token"]
    # 验证新 token 有效（可以在短时间内用它来请求）
    assert new_token is not None
    assert len(new_token) > 0

    # 4. 用新 token 修改密码
    new_headers = {"Authorization": f"Bearer {new_token}"}
    change_response = await client.post(
        "/api/auth/change-password",
        headers=new_headers,
        json={
            "old_password": "password123",
            "new_password": "newpassword456",
        },
    )
    assert change_response.status_code == 200

    # 5. 用新密码登录
    login_response = await client.post(
        "/api/auth/login",
        json={
            "email": "flowtest@example.com",
            "password": "newpassword456",
        },
    )
    assert login_response.status_code == 200
