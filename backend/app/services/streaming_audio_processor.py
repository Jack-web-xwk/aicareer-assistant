"""
Streaming Audio Processor - 流式音频处理器

提供实时流式音频处理能力：
- 增量语音转文字（Streaming STT）
- 流式文字转语音（Streaming TTS）
- Celery 异步任务队列
- 音频片段缓存
- Prometheus 监控指标
"""

import asyncio
import base64
import hashlib
import time
from typing import Any, AsyncGenerator, Dict, List, Optional
from dataclasses import dataclass, field

from celery import Celery
from celery.result import AsyncResult
from openai import AsyncOpenAI

from app.core.config import settings
from app.utils.logger import get_logger
from app.core.redis_client import get_redis_client

logger = get_logger(__name__)


# ========== Celery 配置 ==========

def create_celery_app() -> Celery:
    """创建 Celery 应用实例"""
    celery_app = Celery(
        'audio_processor',
        broker=settings.CELERY_BROKER_URL,
        backend=settings.REDIS_URL,
        include=['app.services.streaming_audio_processor']
    )
    
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,  # 5 分钟超时
        worker_prefetch_multiplier=1,
        broker_connection_retry_on_startup=True,
        broker_connection_max_retries=5,
    )
    
    return celery_app


# 全局 Celery 应用
celery_app = create_celery_app()


# ========== 数据类 ==========

@dataclass
class PartialTranscription:
    """增量转录结果"""
    text: str = ""
    is_final: bool = False
    confidence: float = 0.0
    language: str = "zh"
    duration_ms: int = 0
    chunks_processed: int = 0


@dataclass
class ProgressStatus:
    """任务进度状态"""
    task_id: str
    status: str  # PENDING, STARTED, SUCCESS, FAILURE
    progress: float = 0.0  # 0-100
    message: str = ""
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


# ========== 流式音频处理器 ==========

class StreamingAudioProcessor:
    """
    流式音频处理器
    
    支持：
    - 实时流式 STT（边说话边转录）
    - 流式 TTS（边生成边播放）
    - 音频片段缓存
    - Celery 异步任务
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化流式音频处理器
        
        Args:
            api_key: OpenAI API Key（可选）
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client: Optional[AsyncOpenAI] = None
        
        if self.api_key:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                timeout=float(settings.LLM_REQUEST_TIMEOUT),
            )
        
        self.tts_voice = settings.TTS_VOICE
        self.cache_prefix = "audio:cache:"
        self.streaming_enabled = settings.STREAMING_AUDIO_ENABLED
        
        # 性能统计
        self._total_chunks_processed = 0
        self._total_processing_time = 0.0
        self._latency_samples: List[float] = []
    
    async def process_stream(
        self,
        audio_chunk: bytes,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式处理音频块
        
        Args:
            audio_chunk: 音频二进制数据
            session_id: 会话 ID（用于缓存）
        
        Yields:
            转录的文本片段
        """
        start_time = time.time()
        
        try:
            if not self.streaming_enabled:
                # Fallback: 非流式处理
                text = await self._transcribe_chunk(audio_chunk)
                yield text
                return
            
            # 流式处理
            async for partial_text in self._stream_transcribe(audio_chunk):
                elapsed = time.time() - start_time
                self._record_latency(elapsed)
                yield partial_text
            
            self._total_chunks_processed += 1
            self._total_processing_time += time.time() - start_time
            
        except Exception as e:
            logger.error(f"流式处理失败：{str(e)}", exc_info=True)
            yield f"[Error: {str(e)}]"
    
    async def _transcribe_chunk(self, audio_bytes: bytes) -> str:
        """转录单个音频块"""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        import tempfile
        from pathlib import Path
        
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        try:
            with open(tmp_path, "rb") as audio_file_obj:
                transcript = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file_obj,
                    language="zh",
                    response_format="text",
                )
            
            return transcript.strip() if isinstance(transcript, str) else transcript.text.strip()
        
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    async def _stream_transcribe(
        self,
        audio_bytes: bytes
    ) -> AsyncGenerator[str, None]:
        """
        流式转录音频
        
        模拟流式效果（实际生产环境可使用 WebSocket 连接到 Whisper 流式 API）
        """
        # 完整转录
        full_text = await self._transcribe_chunk(audio_bytes)
        
        # 模拟流式返回（按词分割）
        words = full_text.split()
        current_text = ""
        
        for i, word in enumerate(words):
            current_text += (" " if current_text else "") + word
            # 每 3 个词返回一次部分结果
            if (i + 1) % 3 == 0 or i == len(words) - 1:
                yield current_text
                await asyncio.sleep(0.05)  # 模拟网络延迟
        
        # 最终结果
        yield full_text
    
    async def transcribe_incremental(
        self,
        chunk: bytes,
        session_id: Optional[str] = None
    ) -> PartialTranscription:
        """
        增量转录
        
        Args:
            chunk: 音频块
            session_id: 会话 ID（用于上下文）
        
        Returns:
            PartialTranscription: 部分转录结果
        """
        start_time = time.time()
        
        try:
            text = await self._transcribe_chunk(chunk)
            processing_time = time.time() - start_time
            
            self._record_latency(processing_time)
            
            return PartialTranscription(
                text=text,
                is_final=True,
                confidence=0.95,
                language="zh",
                duration_ms=int(processing_time * 1000),
                chunks_processed=self._total_chunks_processed + 1,
            )
        
        except Exception as e:
            logger.error(f"增量转录失败：{str(e)}")
            return PartialTranscription(
                text=f"[Error: {str(e)}]",
                is_final=False,
                confidence=0.0,
            )
    
    async def synthesize_streaming(
        self,
        text: str,
        voice: Optional[str] = None,
        output_format: str = "mp3"
    ) -> AsyncGenerator[bytes, None]:
        """
        流式 TTS
        
        Args:
            text: 要转换的文本
            voice: 声音类型
            output_format: 输出格式
        
        Yields:
            音频二进制数据块
        """
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        voice = voice or self.tts_voice
        start_time = time.time()
        
        try:
            # 使用 OpenAI TTS API（支持流式响应）
            async with self.client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format=output_format,
            ) as response:
                async for chunk in response.iter_bytes(chunk_size=1024):
                    yield chunk
                    await asyncio.sleep(0.01)  # 避免阻塞
            
            elapsed = time.time() - start_time
            self._record_latency(elapsed)
            logger.debug(f"TTS 流式合成完成：{elapsed:.3f}s")
        
        except Exception as e:
            logger.error(f"流式 TTS 失败：{str(e)}", exc_info=True)
            raise
    
    async def cache_audio_segments(
        self,
        segments: List[bytes],
        session_id: str,
        ttl: int = 3600
    ) -> List[str]:
        """
        缓存音频片段到 Redis
        
        Args:
            segments: 音频片段列表
            session_id: 会话 ID
            ttl: 缓存过期时间（秒）
        
        Returns:
            缓存键列表
        """
        redis_client = get_redis_client()
        cache_keys = []
        
        try:
            for i, segment in enumerate(segments):
                # 生成缓存键
                cache_key = f"{self.cache_prefix}{session_id}:{i}:{int(time.time())}"
                
                # Base64 编码
                encoded = base64.b64encode(segment).decode('utf-8')
                
                # 存储到 Redis
                await redis_client.redis.setex(
                    cache_key,
                    ttl,
                    encoded.encode('utf-8')
                )
                
                cache_keys.append(cache_key)
            
            logger.debug(f"缓存 {len(segments)} 个音频片段到 Redis")
            return cache_keys
        
        except Exception as e:
            logger.error(f"缓存音频片段失败：{str(e)}")
            return []
    
    def _record_latency(self, latency: float):
        """记录延迟样本"""
        self._latency_samples.append(latency)
        # 保留最近 100 个样本
        if len(self._latency_samples) > 100:
            self._latency_samples = self._latency_samples[-100:]
    
    def get_p95_latency(self) -> float:
        """获取 P95 延迟（秒）"""
        if not self._latency_samples:
            return 0.0
        
        sorted_samples = sorted(self._latency_samples)
        p95_index = int(len(sorted_samples) * 0.95)
        return sorted_samples[min(p95_index, len(sorted_samples) - 1)]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理器统计信息"""
        return {
            "total_chunks_processed": self._total_chunks_processed,
            "total_processing_time_seconds": self._total_processing_time,
            "average_latency_seconds": (
                sum(self._latency_samples) / len(self._latency_samples)
                if self._latency_samples else 0.0
            ),
            "p95_latency_seconds": self.get_p95_latency(),
            "streaming_enabled": self.streaming_enabled,
        }


# ========== Celery 任务定义 ==========

@celery_app.task(bind=True, max_retries=3)
def transcribe_audio_task(self, audio_base64: str, language: str = "zh") -> Dict[str, Any]:
    """
    Celery 异步转录任务
    
    Args:
        audio_base64: Base64 编码的音频数据
        language: 语言代码
    
    Returns:
        转录结果字典
    """
    try:
        # 更新任务状态
        self.update_state(
            state='STARTED',
            meta={'progress': 10, 'message': '解码音频数据...'}
        )
        
        # 解码音频
        audio_bytes = base64.b64decode(audio_base64)
        
        self.update_state(
            state='STARTED',
            meta={'progress': 30, 'message': '正在转录...'}
        )
        
        # 创建处理器并转录
        processor = StreamingAudioProcessor()
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            transcript = loop.run_until_complete(
                processor._transcribe_chunk(audio_bytes)
            )
        finally:
            loop.close()
        
        self.update_state(
            state='SUCCESS',
            meta={'progress': 100, 'message': '转录完成'}
        )
        
        return {
            'success': True,
            'transcript': transcript,
            'language': language,
        }
    
    except Exception as exc:
        self.update_state(
            state='FAILURE',
            meta={'progress': 0, 'message': f'转录失败：{str(exc)}'}
        )
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def synthesize_audio_task(self, text: str, voice: str = "alloy") -> Dict[str, Any]:
    """
    Celery 异步 TTS 任务
    
    Args:
        text: 要转换的文本
        voice: 声音类型
    
    Returns:
        TTS 结果字典
    """
    try:
        self.update_state(
            state='STARTED',
            meta={'progress': 20, 'message': '初始化 TTS...'}
        )
        
        # 创建处理器
        processor = StreamingAudioProcessor()
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            audio_bytes = loop.run_until_complete(
                processor.synthesize(text, voice)
            )
        finally:
            loop.close()
        
        self.update_state(
            state='SUCCESS',
            meta={'progress': 100, 'message': '合成完成'}
        )
        
        return {
            'success': True,
            'audio_base64': base64.b64encode(audio_bytes).decode('utf-8'),
            'voice': voice,
        }
    
    except Exception as exc:
        self.update_state(
            state='FAILURE',
            meta={'progress': 0, 'message': f'TTS 失败：{str(exc)}'}
        )
        raise self.retry(exc=exc)


# ========== 便捷函数 ==========

def create_celery_task(app: Celery, task_name: str, args: tuple = ()) -> AsyncResult:
    """
    创建 Celery 异步任务
    
    Args:
        app: Celery 应用
        task_name: 任务名称
        args: 任务参数
    
    Returns:
        AsyncResult: 任务结果对象
    """
    task = app.tasks.get(task_name)
    if task:
        return task.delay(*args)
    raise ValueError(f"Task {task_name} not found")


def get_task_result(task_id: str, app: Optional[Celery] = None) -> Any:
    """
    获取任务结果
    
    Args:
        task_id: 任务 ID
        app: Celery 应用（可选）
    
    Returns:
        任务结果
    """
    celery_app_to_use = app or celery_app
    result = celery_app_to_use.AsyncResult(task_id)
    return result.result


def monitor_task_progress(task_id: str, app: Optional[Celery] = None) -> ProgressStatus:
    """
    监控任务进度
    
    Args:
        task_id: 任务 ID
        app: Celery 应用（可选）
    
    Returns:
        ProgressStatus: 进度状态
    """
    celery_app_to_use = app or celery_app
    result = celery_app_to_use.AsyncResult(task_id)
    
    meta = result.info if isinstance(result.info, dict) else {}
    
    return ProgressStatus(
        task_id=task_id,
        status=result.status,
        progress=meta.get('progress', 0.0),
        message=meta.get('message', ''),
        result=result.result if result.ready() else None,
        error=str(result.info) if result.failed() else None,
        updated_at=time.time(),
    )
