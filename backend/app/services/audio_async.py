"""
Audio Async Wrapper - 异步音频处理封装

根据配置选择同步模式（线程池）或异步模式（Celery）。
- 无 Celery: 使用 asyncio.to_thread 在线程池执行
- 有 Celery: 使用 Celery 任务异步执行
"""

import asyncio
import functools
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from app.utils.logger import get_logger

logger = get_logger(__name__)

# 线程池（限流：最多同时执行 4 个音频任务）
_thread_pool = ThreadPoolExecutor(max_workers=4)


def _run_sync(func, *args, **kwargs):
    """在线程池中运行同步函数"""
    return func(*args, **kwargs)


async def transcribe_audio_async(
    audio_base64: str,
    language: str = "zh",
) -> Dict[str, Any]:
    """
    异步语音转文字

    Args:
        audio_base64: Base64 编码的音频
        language: 语言代码

    Returns:
        {"success": True, "text": "..."} 或 {"success": False, "error": "..."}
    """
    from app.services.audio_tasks import transcribe_audio_sync

    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            _thread_pool,
            functools.partial(transcribe_audio_sync, audio_base64, language),
        )
        logger.debug(f"异步转录完成: {result.get('text', '')[:50]}...")
        return result
    except Exception as e:
        logger.error(f"异步转录异常: {e}")
        return {"success": False, "error": str(e)}


async def synthesize_speech_async(
    text: str,
    voice: str = "alloy",
    output_format: str = "mp3",
    speed: float = 1.0,
) -> Dict[str, Any]:
    """
    异步文字转语音

    Args:
        text: 要转换的文本
        voice: 声音类型
        output_format: 输出格式
        speed: 语速

    Returns:
        {"success": True, "audio_base64": "..."} 或 {"success": False, "error": "..."}
    """
    from app.services.audio_tasks import synthesize_speech_sync

    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            _thread_pool,
            functools.partial(synthesize_speech_sync, text, voice, output_format, speed),
        )
        logger.debug(f"异步合成完成: {len(result.get('audio_base64', ''))} bytes base64")
        return result
    except Exception as e:
        logger.error(f"异步合成异常: {e}")
        return {"success": False, "error": str(e)}
