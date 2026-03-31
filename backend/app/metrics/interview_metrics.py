"""
Interview Metrics - 面试系统监控指标

使用 Prometheus 提供系统性能监控：
- 面试会话统计
- WebSocket 连接监控
- Redis 操作延迟
- 音频处理性能
- LLM 请求指标
"""

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    multiprocess,
    start_http_server,
)
from prometheus_client.registry import REGISTRY
import time
from typing import Dict, Any, Optional
from contextlib import contextmanager

from app.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


# ========== 指标定义 ==========

# ----- 面试会话指标 -----
INTERVIEW_SESSIONS_TOTAL = Counter(
    'interview_sessions_total',
    'Total number of interview sessions',
    ['status', 'job_role']  # status: started, completed, cancelled, failed
)

INTERVIEW_DURATION_SECONDS = Histogram(
    'interview_duration_seconds',
    'Duration of interview sessions in seconds',
    ['job_role', 'difficulty'],
    buckets=(60, 300, 600, 900, 1200, 1800, 2700, 3600, float('inf'))
)

INTERVIEW_QUESTIONS_TOTAL = Counter(
    'interview_questions_total',
    'Total number of questions asked in interviews',
    ['question_type'])

INTERVIEW_SCORE_GAUGE = Gauge(
    'interview_score',
    'Interview scores',
    ['session_id', 'job_role'],
)

INTERVIEW_ACTIVE_SESSIONS = Gauge(
    'interview_active_sessions',
    'Number of active interview sessions',
)


# ----- WebSocket 连接指标 -----
WEBSOCKET_CONNECTIONS = Gauge(
    'websocket_connections',
    'Number of active WebSocket connections',
)

WEBSOCKET_MESSAGES_TOTAL = Counter(
    'websocket_messages_total',
    'Total number of WebSocket messages',
    ['direction'],  # direction: sent, received
)

WEBSOCKET_ERRORS_TOTAL = Counter(
    'websocket_errors_total',
    'Total number of WebSocket errors',
    ['error_type'],
)

WEBSOCKET_LATENCY_SECONDS = Histogram(
    'websocket_latency_seconds',
    'WebSocket message processing latency',
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, float('inf')),
)


# ----- Redis 操作指标 -----
REDIS_OPERATIONS_TOTAL = Counter(
    'redis_operations_total',
    'Total number of Redis operations',
    ['operation', 'status'],  # status: success, failure
)

REDIS_OPERATION_LATENCY = Histogram(
    'redis_operation_latency_seconds',
    'Redis operation latency',
    ['operation'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, float('inf')),
)

REDIS_MEMORY_USAGE = Gauge(
    'redis_memory_usage_bytes',
    'Redis memory usage in bytes',
)

REDIS_CONNECTED_CLIENTS = Gauge(
    'redis_connected_clients',
    'Number of connected Redis clients',
)


# ----- 音频处理指标 -----
AUDIO_PROCESSING_TOTAL = Counter(
    'audio_processing_total',
    'Total number of audio processing requests',
    ['type', 'status'],  # type: stt, tts; status: success, failure
)

AUDIO_PROCESSING_DURATION = Histogram(
    'audio_processing_duration_seconds',
    'Audio processing duration',
    ['type'],
    buckets=(0.1, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, float('inf')),
)

AUDIO_P95_LATENCY = Gauge(
    'audio_p95_latency_seconds',
    'Audio processing P95 latency',
    ['type'],
)

AUDIO_CHUNK_SIZE = Histogram(
    'audio_chunk_size_bytes',
    'Audio chunk size distribution',
    ['type'],
    buckets=(1024, 4096, 16384, 65536, 262144, 1048576, float('inf')),
)


# ----- LLM 请求指标 -----
LLM_REQUESTS_TOTAL = Counter(
    'llm_requests_total',
    'Total number of LLM requests',
    ['provider', 'model', 'status'],
)

LLM_REQUEST_LATENCY = Histogram(
    'llm_request_latency_seconds',
    'LLM request latency',
    ['provider', 'model'],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, float('inf')),
)

LLM_TOKENS_TOTAL = Counter(
    'llm_tokens_total',
    'Total number of tokens used',
    ['provider', 'type'],  # type: prompt, completion
)

LLM_ERRORS_TOTAL = Counter(
    'llm_errors_total',
    'Total number of LLM errors',
    ['provider', 'error_type'],
)


# ----- 系统资源指标 -----
SYSTEM_CPU_PERCENT = Gauge(
    'system_cpu_usage_percent',
    'CPU usage percentage',
)

SYSTEM_MEMORY_PERCENT = Gauge(
    'system_memory_usage_percent',
    'Memory usage percentage',
)

SYSTEM_DISK_USAGE = Gauge(
    'system_disk_usage_bytes',
    'Disk usage in bytes',
    ['mount_point'],
)


# ========== 指标管理器 ==========

class MetricsManager:
    """
    Prometheus 指标管理器
    
    提供统一的指标注册、更新和导出功能。
    """
    
    _instance: Optional["MetricsManager"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        
        self._initialized = True
        self._start_time = time.time()
        self._metrics_endpoint_started = False
    
    def record_interview_start(self, job_role: str):
        """记录面试开始"""
        INTERVIEW_SESSIONS_TOTAL.labels(status='started', job_role=job_role).inc()
        INTERVIEW_ACTIVE_SESSIONS.inc()
        logger.debug(f"记录面试开始：{job_role}")
    
    def record_interview_end(
        self,
        session_id: str,
        job_role: str,
        difficulty: str,
        duration_seconds: float,
        score: Optional[float] = None,
        status: str = 'completed'
    ):
        """记录面试结束"""
        INTERVIEW_SESSIONS_TOTAL.labels(status=status, job_role=job_role).inc()
        INTERVIEW_DURATION_SECONDS.labels(job_role=job_role, difficulty=difficulty).observe(duration_seconds)
        INTERVIEW_ACTIVE_SESSIONS.dec()
        
        if score is not None:
            INTERVIEW_SCORE_GAUGE.labels(session_id=session_id, job_role=job_role).set(score)
        
        logger.debug(f"记录面试结束：{session_id}, duration={duration_seconds}s, score={score}")
    
    def record_websocket_connect(self):
        """记录 WebSocket 连接"""
        WEBSOCKET_CONNECTIONS.inc()
    
    def record_websocket_disconnect(self):
        """记录 WebSocket 断开"""
        WEBSOCKET_CONNECTIONS.dec()
    
    def record_websocket_message(self, direction: str = 'sent'):
        """记录 WebSocket 消息"""
        WEBSOCKET_MESSAGES_TOTAL.labels(direction=direction).inc()
    
    def record_websocket_error(self, error_type: str):
        """记录 WebSocket 错误"""
        WEBSOCKET_ERRORS_TOTAL.labels(error_type=error_type).inc()
    
    @contextmanager
    def track_websocket_latency(self):
        """跟踪 WebSocket 延迟（上下文管理器）"""
        start_time = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            WEBSOCKET_LATENCY_SECONDS.observe(elapsed)
    
    def record_redis_operation(
        self,
        operation: str,
        latency_seconds: float,
        success: bool = True
    ):
        """记录 Redis 操作"""
        status = 'success' if success else 'failure'
        REDIS_OPERATIONS_TOTAL.labels(operation=operation, status=status).inc()
        REDIS_OPERATION_LATENCY.labels(operation=operation).observe(latency_seconds)
    
    def record_audio_processing(
        self,
        audio_type: str,
        duration_seconds: float,
        success: bool = True,
        chunk_size_bytes: Optional[int] = None
    ):
        """记录音频处理"""
        status = 'success' if success else 'failure'
        AUDIO_PROCESSING_TOTAL.labels(type=audio_type, status=status).inc()
        AUDIO_PROCESSING_DURATION.labels(type=audio_type).observe(duration_seconds)
        
        if chunk_size_bytes:
            AUDIO_CHUNK_SIZE.labels(type=audio_type).observe(chunk_size_bytes)
    
    def update_audio_p95_latency(self, audio_type: str, latency_seconds: float):
        """更新音频 P95 延迟"""
        AUDIO_P95_LATENCY.labels(type=audio_type).set(latency_seconds)
    
    def record_llm_request(
        self,
        provider: str,
        model: str,
        latency_seconds: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        success: bool = True,
        error_type: Optional[str] = None
    ):
        """记录 LLM 请求"""
        status = 'success' if success else 'failure'
        LLM_REQUESTS_TOTAL.labels(provider=provider, model=model, status=status).inc()
        LLM_REQUEST_LATENCY.labels(provider=provider, model=model).observe(latency_seconds)
        
        if prompt_tokens > 0:
            LLM_TOKENS_TOTAL.labels(provider=provider, type='prompt').inc(prompt_tokens)
        
        if completion_tokens > 0:
            LLM_TOKENS_TOTAL.labels(provider=provider, type='completion').inc(completion_tokens)
        
        if not success and error_type:
            LLM_ERRORS_TOTAL.labels(provider=provider, error_type=error_type).inc()
    
    def update_system_metrics(
        self,
        cpu_percent: float,
        memory_percent: float,
        disk_usage_bytes: Dict[str, int] = None
    ):
        """更新系统资源指标"""
        SYSTEM_CPU_PERCENT.set(cpu_percent)
        SYSTEM_MEMORY_PERCENT.set(memory_percent)
        
        if disk_usage_bytes:
            for mount_point, usage in disk_usage_bytes.items():
                SYSTEM_DISK_USAGE.labels(mount_point=mount_point).set(usage)
    
    def get_metrics(self) -> str:
        """获取所有指标的文本格式"""
        return generate_latest(REGISTRY).decode('utf-8')
    
    async def start_metrics_server(self, port: int = 8000):
        """启动 metrics HTTP 服务器"""
        if self._metrics_endpoint_started:
            return
        
        try:
            start_http_server(port)
            self._metrics_endpoint_started = True
            logger.info(f"Prometheus metrics server started on port {port}")
        except Exception as e:
            logger.error(f"启动 metrics 服务器失败：{e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        return {
            "uptime_seconds": time.time() - self._start_time,
            "active_interviews": INTERVIEW_ACTIVE_SESSIONS._value.get(),
            "websocket_connections": WEBSOCKET_CONNECTIONS._value.get(),
            "total_interviews_started": INTERVIEW_SESSIONS_TOTAL._labels.get(('started', ''), {})._value.sum() if hasattr(INTERVIEW_SESSIONS_TOTAL, '_labels') else 0,
            "total_audio_processed": AUDIO_PROCESSING_TOTAL._labels.get(('stt', 'success'), {})._value.sum() if hasattr(AUDIO_PROCESSING_TOTAL, '_labels') else 0,
        }


# ========== 便捷函数 ==========

def get_metrics_manager() -> MetricsManager:
    """获取指标管理器单例"""
    return MetricsManager()


def generate_metrics() -> str:
    """生成 Prometheus 格式的指标数据"""
    return get_metrics_manager().get_metrics()


def get_metrics_content_type() -> str:
    """获取 metrics 内容类型"""
    return CONTENT_TYPE_LATEST


@contextmanager
def track_metric_duration(metric, **labels):
    """
    跟踪指标延迟的通用上下文管理器
    
    Usage:
        with track_metric_duration(LLM_REQUEST_LATENCY, provider='openai', model='gpt-4'):
            # 执行操作
            pass
    """
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        if labels:
            metric.labels(**labels).observe(elapsed)
        else:
            metric.observe(elapsed)


# ========== FastAPI 集成 ==========

def setup_metrics_endpoint(app=None):
    """
    在 FastAPI 应用中设置 metrics 端点
    
    Args:
        app: FastAPI 应用实例
    """
    from fastapi import Response
    
    if app is None:
        logger.warning("无法设置 metrics 端点：app 为 None")
        return
    
    @app.get("/metrics", tags=["monitoring"])
    async def metrics_endpoint():
        """Prometheus metrics endpoint"""
        return Response(
            content=generate_metrics(),
            media_type=CONTENT_TYPE_LATEST,
        )
    
    logger.info("Metrics endpoint registered at /metrics")


# 全局指标管理器实例
metrics_manager = MetricsManager()
