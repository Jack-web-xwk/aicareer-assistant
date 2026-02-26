"""
Pytest Configuration - 测试配置

提供测试 fixtures 和配置。
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.database import Base, get_db
from app.core.config import settings


# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    创建测试数据库会话
    
    每个测试函数使用独立的内存数据库。
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    创建测试客户端
    """
    from main import app
    
    # 覆盖数据库依赖
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_resume_text() -> str:
    """示例简历文本"""
    return """
    张三
    Python 后端工程师
    
    联系方式：
    邮箱：zhangsan@example.com
    电话：13800138000
    
    教育背景：
    北京大学 | 计算机科学与技术 | 硕士 | 2018-2021
    清华大学 | 软件工程 | 学士 | 2014-2018
    
    工作经历：
    字节跳动 | 高级后端工程师 | 2021-至今
    - 负责抖音推荐系统后端开发
    - 优化接口性能，QPS 提升 200%
    - 设计高可用架构，系统可用性达 99.99%
    
    技术栈：
    - Python, Go, Java
    - FastAPI, Django, Flask
    - MySQL, Redis, MongoDB
    - Kubernetes, Docker
    """


@pytest.fixture
def sample_job_description() -> str:
    """示例岗位描述"""
    return """
    Python 后端工程师
    
    职责：
    - 负责后端系统的设计与开发
    - 参与系统架构设计和技术选型
    - 编写高质量、可维护的代码
    
    要求：
    - 3年以上 Python 开发经验
    - 熟悉 FastAPI/Django/Flask 框架
    - 熟悉 MySQL、Redis 等数据库
    - 有大型项目经验优先
    
    加分项：
    - 有分布式系统开发经验
    - 熟悉 Kubernetes
    - 有 AI/ML 相关经验
    """
