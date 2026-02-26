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
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    
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
