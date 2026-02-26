"""
Application Configuration - 应用配置

使用 Pydantic Settings 管理环境变量和应用配置。
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用配置类
    
    从环境变量或 .env 文件读取配置，支持类型验证和默认值。
    """
    
    # ========== LLM Provider Configuration ==========
    # 通用 LLM 配置（优先级最高）
    LLM_PROVIDER: str = "deepseek"  # openai, deepseek, zhipu, ollama, anthropic, qwen
    LLM_MODEL: str = ""           # 留空则使用各提供商默认模型
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # DeepSeek Configuration
    DEEPSEEK_API_KEY: str = "sk-3c374bea34474a5196427330fdfaddd4"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    # 智谱 GLM Configuration
    ZHIPU_API_KEY: str = ""
    ZHIPU_MODEL: str = "glm-4-flash"
    
    # Ollama Configuration (本地模型)
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_API_KEY: str = "ollama"  # Ollama 不需要真实 key
    OLLAMA_MODEL: str = "llama3.2"
    
    # Anthropic Claude Configuration
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # 通义千问 Qwen Configuration
    QWEN_API_KEY: str = ""
    QWEN_MODEL: str = "qwen-turbo"
    
    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/career_assistant.db"
    
    # Application Settings
    APP_NAME: str = "AI Career Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # CORS Settings
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # File Upload Settings
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "./uploads"
    
    # Audio Processing Settings
    AUDIO_FORMAT: str = "mp3"
    TTS_VOICE: str = "alloy"  # OpenAI TTS voices: alloy, echo, fable, onyx, nova, shimmer
    
    # Interview Settings
    MAX_INTERVIEW_QUESTIONS: int = 5
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """将 CORS_ORIGINS 字符串转换为列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def max_upload_size_bytes(self) -> int:
        """将 MB 转换为字节"""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """
    获取配置单例
    
    使用 lru_cache 确保配置只加载一次。
    """
    return Settings()


# 全局配置实例
settings = get_settings()
