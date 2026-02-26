"""
Health Check API - 健康检查接口

提供服务健康状态检查和 LLM 配置信息。
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.llm_provider import LLMFactory, LLMProvider, get_llm_info
from app.models.schemas import SuccessResponse

router = APIRouter()


@router.get("", response_model=SuccessResponse)
async def health_check():
    """
    基础健康检查
    
    返回服务基本状态和版本信息。
    """
    return SuccessResponse(
        success=True,
        message="Service is healthy",
        data={
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@router.get("/db", response_model=SuccessResponse)
async def database_health_check(db: AsyncSession = Depends(get_db)):
    """
    数据库健康检查
    
    检查数据库连接是否正常。
    """
    try:
        # 执行简单查询测试数据库连接
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        
        return SuccessResponse(
            success=True,
            message="Database connection is healthy",
            data={
                "database": "connected",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception as e:
        return SuccessResponse(
            success=False,
            message=f"Database connection failed: {str(e)}",
            data={
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@router.get("/ready", response_model=SuccessResponse)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    就绪检查
    
    检查服务是否准备好接收请求。
    """
    checks = {
        "database": False,
        "llm_api_key": False,
    }
    
    # 检查数据库
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        checks["database"] = True
    except Exception:
        pass
    
    # 检查 LLM API Key (根据当前配置的提供商)
    try:
        provider_str = settings.LLM_PROVIDER.lower()
        provider = LLMProvider(provider_str)
        api_key = LLMFactory.get_api_key(provider)
        # Ollama 不需要真实的 API Key
        checks["llm_api_key"] = bool(api_key) or provider == LLMProvider.OLLAMA
    except Exception:
        # 默认检查 OpenAI
        checks["llm_api_key"] = bool(settings.OPENAI_API_KEY)
    
    all_ready = all(checks.values())
    
    return SuccessResponse(
        success=all_ready,
        message="Service is ready" if all_ready else "Service is not fully ready",
        data={
            "ready": all_ready,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@router.get("/llm", response_model=SuccessResponse)
async def llm_config():
    """
    LLM 配置信息
    
    返回当前 LLM 提供商配置和可用模型列表。
    """
    llm_info = get_llm_info()
    
    # 检查 API Key 是否配置
    try:
        provider = LLMProvider(llm_info["provider"])
        api_key = LLMFactory.get_api_key(provider)
        has_api_key = bool(api_key) or provider == LLMProvider.OLLAMA
    except Exception:
        has_api_key = False
    
    return SuccessResponse(
        success=True,
        message="LLM configuration",
        data={
            **llm_info,
            "api_key_configured": has_api_key,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@router.get("/llm/providers", response_model=SuccessResponse)
async def list_llm_providers():
    """
    列出所有支持的 LLM 提供商
    
    返回所有可用的提供商及其支持的模型。
    """
    providers_info = {}
    
    for provider in LLMProvider:
        providers_info[provider.value] = {
            "models": LLMFactory.list_models(provider),
            "default_model": LLMFactory.get_default_model(provider),
        }
    
    return SuccessResponse(
        success=True,
        message="Available LLM providers",
        data={
            "providers": providers_info,
            "current_provider": settings.LLM_PROVIDER,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
