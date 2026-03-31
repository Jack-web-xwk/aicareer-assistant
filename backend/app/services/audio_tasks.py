"""
Audio Async Tasks - 异步音频处理

使用 Celery 任务队列处理 Whisper 转录和 TTS 合成，避免阻塞事件循环。
"""

import base64
import tempfile
from pathlib import Path
from typing import Optional

from app.core.config import settings


def _get_openai_client():
    """延迟导入 OpenAI 客户端"""
    from openai import OpenAI
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OpenAI API Key is required")
    return OpenAI(api_key=api_key, timeout=float(settings.LLM_REQUEST_TIMEOUT))


def transcribe_audio_sync(
    audio_base64: str,
    language: str = "zh",
) -> dict:
    """
    同步版语音转文字（Celery worker 调用）

    Args:
        audio_base64: Base64 编码的音频数据
        language: 语言代码

    Returns:
        {"success": True, "text": "..."} 或 {"success": False, "error": "..."}
    """
    try:
        client = _get_openai_client()
        audio_data = base64.b64decode(audio_base64)

        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as f:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language=language,
                    response_format="text",
                )
            text = transcript.strip() if isinstance(transcript, str) else transcript.text.strip()
            return {"success": True, "text": text}
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    except Exception as e:
        return {"success": False, "error": str(e)}


def synthesize_speech_sync(
    text: str,
    voice: str = "alloy",
    output_format: str = "mp3",
    speed: float = 1.0,
) -> dict:
    """
    同步版文字转语音（Celery worker 调用）

    Args:
        text: 要转换的文本
        voice: 声音类型
        output_format: 输出格式
        speed: 语速

    Returns:
        {"success": True, "audio_base64": "..."} 或 {"success": False, "error": "..."}
    """
    try:
        client = _get_openai_client()

        if voice not in {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}:
            voice = "alloy"

        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            response_format=output_format,
            speed=speed,
        )

        audio_b64 = base64.b64encode(response.content).decode("utf-8")
        return {"success": True, "audio_base64": audio_b64}

    except Exception as e:
        return {"success": False, "error": str(e)}
