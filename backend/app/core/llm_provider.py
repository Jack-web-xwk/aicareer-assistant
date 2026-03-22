"""
LLM Provider - 多模型支持

统一管理多种 LLM 提供商，支持：
- OpenAI (GPT-4o, GPT-4, GPT-3.5)
- DeepSeek (deepseek-chat, deepseek-coder, deepseek-reasoner)
- 智谱 GLM (glm-4, glm-4-flash)
- Ollama (本地模型)
- Anthropic Claude (claude-3-opus, claude-3-sonnet)
- 通义千问 Qwen (qwen-turbo, qwen-plus, qwen-max)
- 阿里百炼 Bailian (Qwen 系列模型)
"""

from enum import Enum
from typing import Optional, Dict, Any, Union

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import settings


class LLMProvider(str, Enum):
    """LLM 提供商枚举"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    ZHIPU = "zhipu"           # 智谱 GLM
    OLLAMA = "ollama"         # 本地模型
    ANTHROPIC = "anthropic"   # Claude
    QWEN = "qwen"             # 通义千问
    BAILIAN = "bailian"       # 阿里百炼


# 各提供商的 API Base URL
PROVIDER_BASE_URLS: Dict[LLMProvider, str] = {
    LLMProvider.OPENAI: "https://api.openai.com/v1",
    LLMProvider.DEEPSEEK: "https://api.deepseek.com",
    LLMProvider.ZHIPU: "https://open.bigmodel.cn/api/paas/v4",
    LLMProvider.OLLAMA: "http://localhost:11434/v1",
    LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1",
    LLMProvider.QWEN: "https://dashscope.aliyuncs.com/compatible-mode/v1",
    LLMProvider.BAILIAN: "https://dashscope.aliyuncs.com/compatible-mode/v1",
}


# 各提供商的默认模型
PROVIDER_DEFAULT_MODELS: Dict[LLMProvider, str] = {
    LLMProvider.OPENAI: "gpt-4o-mini",
    LLMProvider.DEEPSEEK: "deepseek-chat",
    LLMProvider.ZHIPU: "glm-4-flash",
    LLMProvider.OLLAMA: "llama3.2",
    LLMProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
    LLMProvider.QWEN: "qwen-turbo",
    LLMProvider.BAILIAN: "qwen-plus",
}


# 各提供商支持的模型列表
PROVIDER_MODELS: Dict[LLMProvider, list] = {
    LLMProvider.OPENAI: [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        "o1",
        "o1-mini",
        "o1-preview",
    ],
    LLMProvider.DEEPSEEK: [
        "deepseek-chat",        # DeepSeek-V3 通用对话
        "deepseek-coder",       # 代码专用
        "deepseek-reasoner",    # R1 推理模型
    ],
    LLMProvider.ZHIPU: [
        "glm-4-plus",
        "glm-4-0520",
        "glm-4",
        "glm-4-air",
        "glm-4-airx",
        "glm-4-long",
        "glm-4-flash",
        "glm-4v",               # 视觉模型
        "glm-4v-plus",
        "codegeex-4",           # 代码模型
    ],
    LLMProvider.OLLAMA: [
        "llama3.2",
        "llama3.1",
        "qwen2.5",
        "qwen2.5-coder",
        "deepseek-coder-v2",
        "mistral",
        "codellama",
        "phi3",
    ],
    LLMProvider.ANTHROPIC: [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ],
    LLMProvider.QWEN: [
        "qwen-turbo",
        "qwen-plus",
        "qwen-max",
        "qwen-long",
        "qwen-vl-plus",        # 视觉模型
        "qwen-vl-max",
        "qwen-image-edit-plus",
        "qwen-image-edit-plus-2025-10-30",
        "qwen-coder-turbo",    # 代码模型
    ],
    LLMProvider.BAILIAN: [
        "qwen-turbo",
        "qwen-plus",
        "qwen-max",
        "qwen-long",
        "qwen-vl-plus",
        "qwen-vl-max",
        "qwen-image-edit-plus",
        "qwen-image-edit-plus-2025-10-30",
        "qwen-coder-turbo",
    ],
}


class LLMFactory:
    """
    LLM 工厂类
    
    统一创建和管理不同提供商的 LLM 实例。
    
    Usage:
        # 使用默认配置
        llm = LLMFactory.create()
        
        # 指定提供商
        llm = LLMFactory.create(provider=LLMProvider.DEEPSEEK)
        
        # 完全自定义
        llm = LLMFactory.create(
            provider=LLMProvider.DEEPSEEK,
            model="deepseek-reasoner",
            api_key="your-api-key",
            temperature=0.7,
        )
    """
    
    @staticmethod
    def _clean_api_key(raw_key: Optional[str]) -> str:
        """清洗 API Key，避免因引号/空白导致鉴权失败。"""
        if not raw_key:
            return ""
        cleaned = raw_key.strip().strip('"').strip("'").strip()
        # 常见占位值视为未配置
        if cleaned.startswith("your-") or "your-" in cleaned.lower():
            return ""
        return cleaned

    @staticmethod
    def get_api_key(provider: LLMProvider) -> str:
        """获取指定提供商的 API Key"""
        key_mapping = {
            LLMProvider.OPENAI: LLMFactory._clean_api_key(settings.OPENAI_API_KEY),
            LLMProvider.DEEPSEEK: LLMFactory._clean_api_key(settings.DEEPSEEK_API_KEY),
            LLMProvider.ZHIPU: LLMFactory._clean_api_key(settings.ZHIPU_API_KEY),
            LLMProvider.OLLAMA: LLMFactory._clean_api_key(settings.OLLAMA_API_KEY),
            LLMProvider.ANTHROPIC: LLMFactory._clean_api_key(settings.ANTHROPIC_API_KEY),
            LLMProvider.QWEN: LLMFactory._clean_api_key(settings.QWEN_API_KEY),
            # Bailian 与 Qwen 都走 DashScope 兼容接口，允许互为兜底
            LLMProvider.BAILIAN: (
                LLMFactory._clean_api_key(settings.BAILIAN_API_KEY)
                or LLMFactory._clean_api_key(settings.QWEN_API_KEY)
            ),
        }
        # 默认提供 deepseek
        return key_mapping.get(provider, LLMFactory._clean_api_key(settings.DEEPSEEK_API_KEY))
    
    @staticmethod
    def get_base_url(provider: LLMProvider, custom_url: Optional[str] = None) -> str:
        """获取指定提供商的 Base URL"""
        if custom_url:
            return custom_url
        
        # Ollama 使用配置中的 URL
        if provider == LLMProvider.OLLAMA:
            return settings.OLLAMA_BASE_URL
        # Bailian 使用配置中的 URL
        if provider == LLMProvider.BAILIAN:
            return settings.BAILIAN_BASE_URL
        
        return PROVIDER_BASE_URLS.get(provider, PROVIDER_BASE_URLS[LLMProvider.DEEPSEEK])
    
    @staticmethod
    def get_default_model(provider: LLMProvider) -> str:
        """获取指定提供商的默认模型"""
        return PROVIDER_DEFAULT_MODELS.get(provider, "deepseek-chat")
    
    @staticmethod
    def create(
        provider: Optional[Union[LLMProvider, str]] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> BaseChatModel:
        """
        创建 LLM 实例
        
        Args:
            provider: LLM 提供商 (默认从配置读取)
            model: 模型名称 (默认使用提供商的默认模型)
            api_key: API Key (默认从配置读取)
            base_url: API Base URL (默认使用提供商的标准 URL)
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他传递给 ChatOpenAI 的参数
        
        Returns:
            BaseChatModel 实例
        
        Raises:
            ValueError: 当提供商不支持或 API Key 缺失时
        """
        # 解析 provider
        if provider is None:
            provider_str = settings.LLM_PROVIDER.lower()
            try:
                provider = LLMProvider(provider_str)
            except ValueError:
                provider = LLMProvider.OPENAI
        elif isinstance(provider, str):
            try:
                provider = LLMProvider(provider.lower())
            except ValueError:
                raise ValueError(f"不支持的 LLM 提供商: {provider}")
        
        # 获取配置
        final_api_key = api_key or LLMFactory.get_api_key(provider)
        final_base_url = base_url or LLMFactory.get_base_url(provider)
        final_model = model or settings.LLM_MODEL or LLMFactory.get_default_model(provider)
        
        # Ollama 不需要 API Key
        if provider != LLMProvider.OLLAMA and not final_api_key:
            raise ValueError(f"缺少 {provider.value} 的 API Key，请在环境变量中配置")
        
        # 构建参数
        llm_params: Dict[str, Any] = {
            "model": final_model,
            "temperature": temperature,
            **kwargs,
        }
        llm_params.setdefault("request_timeout", settings.LLM_REQUEST_TIMEOUT)
        
        if final_api_key:
            llm_params["api_key"] = final_api_key
        
        if final_base_url:
            llm_params["base_url"] = final_base_url
        
        if max_tokens:
            llm_params["max_tokens"] = max_tokens
        
        # Anthropic 需要特殊处理 header
        if provider == LLMProvider.ANTHROPIC:
            llm_params["default_headers"] = {
                "anthropic-version": "2023-06-01",
            }
        
        # 所有支持的提供商都兼容 OpenAI API 格式
        return ChatOpenAI(**llm_params)
    
    @staticmethod
    def create_for_interview(
        provider: Optional[Union[LLMProvider, str]] = None,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> BaseChatModel:
        """
        创建面试场景专用 LLM
        
        面试场景特点：需要更自然的对话、适度的创造性
        """
        temperature = kwargs.pop("temperature", 0.7)
        return LLMFactory.create(
            provider=provider,
            model=model,
            temperature=temperature,
            **kwargs,
        )
    
    @staticmethod
    def create_for_resume(
        provider: Optional[Union[LLMProvider, str]] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> BaseChatModel:
        """
        创建简历优化场景专用 LLM
        
        简历场景特点：需要更精准的信息提取、较低的创造性
        """
        kwargs.pop("temperature", None)  # 避免与显式参数重复传入 create
        return LLMFactory.create(
            provider=provider,
            model=model,
            temperature=temperature,
            **kwargs,
        )
    
    @staticmethod
    def list_providers() -> list:
        """列出所有支持的提供商"""
        return [p.value for p in LLMProvider]
    
    @staticmethod
    def list_models(provider: Union[LLMProvider, str]) -> list:
        """列出指定提供商支持的模型"""
        if isinstance(provider, str):
            provider = LLMProvider(provider.lower())
        return PROVIDER_MODELS.get(provider, [])


# 便捷函数
def create_llm(
    provider: Optional[Union[LLMProvider, str]] = None,
    model: Optional[str] = None,
    **kwargs: Any,
) -> BaseChatModel:
    """
    创建 LLM 实例的便捷函数
    
    Args:
        provider: LLM 提供商
        model: 模型名称
        **kwargs: 其他参数
    
    Returns:
        BaseChatModel 实例
    """
    return LLMFactory.create(provider=provider, model=model, **kwargs)


def get_llm_info() -> Dict[str, Any]:
    """
    获取当前 LLM 配置信息
    
    Returns:
        包含提供商、模型等信息的字典
    """
    provider_str = settings.LLM_PROVIDER.lower()
    try:
        provider = LLMProvider(provider_str)
    except ValueError:
        provider = LLMProvider.OPENAI
    
    return {
        "provider": provider.value,
        "model": settings.LLM_MODEL or LLMFactory.get_default_model(provider),
        "available_providers": LLMFactory.list_providers(),
        "available_models": LLMFactory.list_models(provider),
    }
