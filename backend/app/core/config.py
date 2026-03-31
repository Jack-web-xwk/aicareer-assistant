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
    LLM_PROVIDER: str = "deepseek"  # openai, deepseek, zhipu, ollama, anthropic, qwen, bailian
    LLM_MODEL: str = ""           # 留空则使用各提供商默认模型
    LLM_REQUEST_TIMEOUT: int = 120  # 单次 LLM 请求超时（秒）
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # DeepSeek Configuration
    DEEPSEEK_API_KEY: str = ""
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

    # 阿里百炼 Bailian Configuration
    BAILIAN_API_KEY: str = ""
    BAILIAN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    BAILIAN_MODEL: str = "qwen-plus"
    
    # Database Configuration
    # 开发: sqlite+aiosqlite:///./data/career_assistant.db
    # 生产: postgresql+asyncpg://user:pass@localhost:5432/aicareer
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/career_assistant.db"
    
    # Application Settings
    APP_NAME: str = "AI Career Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # CORS Settings
    # 生产环境请设置为实际的前端域名，不要使用通配符 *
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
    
    # File Upload Settings
    MAX_UPLOAD_SIZE_MB: int = 10
    UPLOAD_DIR: str = "./uploads"
    
    # Audio Processing Settings
    AUDIO_FORMAT: str = "mp3"
    TTS_VOICE: str = "alloy"  # OpenAI TTS voices: alloy, echo, fable, onyx, nova, shimmer
    
    # Interview Settings
    MAX_INTERVIEW_QUESTIONS: int = 5

    # ========== Redis Configuration ==========
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_SIZE: int = 50
    REDIS_SOCKET_TIMEOUT: float = 5.0
    REDIS_CONNECT_TIMEOUT: float = 5.0
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_MAX_RETRIES: int = 3

    # ========== Celery Configuration ==========
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_TIMEZONE: str = "UTC"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 300  # 5 minutes

    # ========== WebSocket Configuration ==========
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30  # seconds
    WEBSOCKET_MAX_CONNECTIONS_PER_USER: int = 5
    WEBSOCKET_MAX_RECONNECT_RETRIES: int = 3
    WEBSOCKET_ORPHAN_TIMEOUT: int = 300  # 5 minutes

    # ========== JWT Configuration ==========
    JWT_SECRET_KEY: str = ""  # 留空则自动生成随机字符串

    # ========== Streaming Audio Configuration ==========
    STREAMING_AUDIO_ENABLED: bool = True
    STREAMING_AUDIO_CHUNK_DURATION_MS: int = 1000
    STREAMING_AUDIO_CACHE_TTL: int = 3600  # 1 hour

    # ========== Prometheus Metrics Configuration ==========
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = 8000
    METRICS_ENDPOINT: str = "/metrics"

    # ========== Performance Configuration ==========
    PERFORMANCE_PROFILING_ENABLED: bool = False
    SLOW_QUERY_THRESHOLD_MS: int = 1000
    SLOW_API_THRESHOLD_MS: int = 2000

    # Job search (crawler aggregation)
    JOB_SEARCH_RATE_LIMIT_PER_MINUTE: int = 10
    JOB_SEARCH_CACHE_TTL_SECONDS: float = 300.0

    # 岗位链接爬取：直连 HTML 失败或结构为空时，尝试 Jina Reader 拉取正文（参考 mp 文档分层思路）
    JOB_SCRAPE_JINA_READER_FALLBACK: bool = True
    JINA_READER_BASE_URL: str = "https://r.jina.ai"
    JINA_API_KEY: str = ""  # 可选，提高额度时在 https://jina.ai 获取

    # Scrapling（curl 指纹 / 反爬）：需 pip install "scrapling[fetchers]"；默认关闭
    JOB_SCRAPE_SCRAPLING_FALLBACK: bool = False
    JOB_SCRAPE_SCRAPLING_VERIFY_SSL: bool = True

    # 截图识别岗位：多模态模型（失败自动换下一模型；默认优先 BAILIAN → QWEN → OpenAI → 智谱）
    JOB_SCREENSHOT_MAX_IMAGE_MB: int = 8
    JOB_SCREENSHOT_VISION_PROVIDER: str = ""
    JOB_SCREENSHOT_VISION_MODEL: str = ""
    # 逗号分隔，追加在 DashScope 默认链之后尝试（如控制台里其它视觉模型名）
    JOB_SCREENSHOT_VISION_MODEL_FALLBACKS: str = ""

    # Boss 直聘详情：服务器/机房 IP 常被 WAPI 返回 code=35。
    # 配置方式（二选一，推荐 A）：
    # A) F12 → Network → 点开任意 www.zhipin.com 的文档或 XHR → Request Headers →
    #    复制整行「Cookie:」后面的内容（一行内 name=value; 用分号+空格连接），粘贴到本变量。
    # B) 若只有 Application → Cookies 表格：把同一域名下条目拼成「name=value; name2=value2」
    #    至少应包含 __zp_stoken__；通常还需 wt2、bst、__a、__l、lastCity 等同次会话字段。
    # 勿提交到 Git；仅写在本地 .env（已 .gitignore）。
    BOSS_ZHIPIN_EXTRA_COOKIES: str = ""

    # Resume optimization: on startup, resume rows still in optimizing (e.g. after crash)
    RESUME_OPTIMIZATION_RECOVERY_ON_STARTUP: bool = True

    # Resume study QA: LLM-generated interview-prep questions from optimized task context
    RESUME_STUDY_QA_MAX_ITEMS: int = 8
    # Empty = use LLM_MODEL; any DashScope compatible name when provider is bailian
    RESUME_STUDY_QA_MODEL: str = ""
    # Empty = use LLM_PROVIDER; set bailian to force 百炼 for study QA only
    RESUME_STUDY_QA_PROVIDER: str = ""

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
    s = Settings()
    # 自动生成 JWT 密钥（如果未配置）
    if not s.JWT_SECRET_KEY:
        import secrets
        s.JWT_SECRET_KEY = secrets.token_urlsafe(64)
    return s


# 全局配置实例
settings = get_settings()
