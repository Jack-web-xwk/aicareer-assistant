"""
Audio Processor Service - 音频处理服务

使用 OpenAI Whisper 和 TTS 实现语音转文字和文字转语音。
"""

import base64
import io
import tempfile
from pathlib import Path
from typing import Optional, Union

from openai import OpenAI

from app.core.config import settings
from app.core.exceptions import AIServiceException


class AudioProcessor:
    """
    音频处理器
    
    使用 OpenAI Whisper API 进行语音转文字（STT）
    使用 OpenAI TTS API 进行文字转语音
    """
    
    # 支持的音频格式
    SUPPORTED_AUDIO_FORMATS = {"mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"}
    
    # TTS 可用的声音
    AVAILABLE_VOICES = {"alloy", "echo", "fable", "onyx", "nova", "shimmer"}
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化音频处理器
        
        Args:
            api_key: OpenAI API Key，默认从配置读取
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API Key is required")
        
        self.client = OpenAI(
            api_key=self.api_key,
            timeout=float(settings.LLM_REQUEST_TIMEOUT),
        )
        self.tts_voice = settings.TTS_VOICE
    
    def transcribe(
        self,
        audio_file: Optional[Union[str, Path]] = None,
        audio_bytes: Optional[bytes] = None,
        audio_base64: Optional[str] = None,
        language: str = "zh",
    ) -> str:
        """
        语音转文字（Whisper）
        
        Args:
            audio_file: 音频文件路径
            audio_bytes: 音频二进制数据
            audio_base64: Base64 编码的音频数据
            language: 语言代码（zh, en 等）
        
        Returns:
            转录的文本
        
        Raises:
            AIServiceException: 转录失败
        """
        try:
            # 处理不同的输入类型
            if audio_file:
                file_path = Path(audio_file)
                with open(file_path, "rb") as f:
                    audio_data = f.read()
                filename = file_path.name
            elif audio_bytes:
                audio_data = audio_bytes
                filename = "audio.webm"
            elif audio_base64:
                audio_data = base64.b64decode(audio_base64)
                filename = "audio.webm"
            else:
                raise ValueError("No audio input provided")
            
            # 创建临时文件（OpenAI API 需要文件对象）
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name
            
            try:
                # 调用 Whisper API
                with open(tmp_path, "rb") as audio_file_obj:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file_obj,
                        language=language,
                        response_format="text",
                    )
                
                return transcript.strip() if isinstance(transcript, str) else transcript.text.strip()
            
            finally:
                # 清理临时文件
                Path(tmp_path).unlink(missing_ok=True)
        
        except Exception as e:
            raise AIServiceException(
                f"Speech-to-text failed: {str(e)}",
                model="whisper-1",
                operation="transcribe",
            )
    
    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        output_format: str = "mp3",
        speed: float = 1.0,
    ) -> bytes:
        """
        文字转语音（TTS）
        
        Args:
            text: 要转换的文本
            voice: 声音类型（alloy, echo, fable, onyx, nova, shimmer）
            output_format: 输出格式（mp3, opus, aac, flac）
            speed: 语速（0.25 到 4.0）
        
        Returns:
            音频二进制数据
        
        Raises:
            AIServiceException: 合成失败
        """
        try:
            voice = voice or self.tts_voice
            
            if voice not in self.AVAILABLE_VOICES:
                voice = "alloy"
            
            # 调用 TTS API
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format=output_format,
                speed=speed,
            )
            
            # 读取音频数据
            audio_data = response.content
            
            return audio_data
        
        except Exception as e:
            raise AIServiceException(
                f"Text-to-speech failed: {str(e)}",
                model="tts-1",
                operation="synthesize",
            )
    
    def synthesize_to_base64(
        self,
        text: str,
        voice: Optional[str] = None,
        output_format: str = "mp3",
        speed: float = 1.0,
    ) -> str:
        """
        文字转语音并返回 Base64 编码
        
        Args:
            text: 要转换的文本
            voice: 声音类型
            output_format: 输出格式
            speed: 语速
        
        Returns:
            Base64 编码的音频数据
        """
        audio_bytes = self.synthesize(text, voice, output_format, speed)
        return base64.b64encode(audio_bytes).decode("utf-8")
    
    def save_audio(
        self,
        audio_data: Union[bytes, str],
        output_path: Union[str, Path],
    ) -> Path:
        """
        保存音频到文件
        
        Args:
            audio_data: 音频数据（bytes 或 base64 字符串）
            output_path: 输出文件路径
        
        Returns:
            保存的文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(audio_data, str):
            audio_data = base64.b64decode(audio_data)
        
        with open(output_path, "wb") as f:
            f.write(audio_data)
        
        return output_path


# 便捷函数
def transcribe_audio(
    audio_file: Optional[Union[str, Path]] = None,
    audio_bytes: Optional[bytes] = None,
    audio_base64: Optional[str] = None,
    language: str = "zh",
) -> str:
    """
    语音转文字的便捷函数
    
    Args:
        audio_file: 音频文件路径
        audio_bytes: 音频二进制数据
        audio_base64: Base64 编码的音频数据
        language: 语言代码
    
    Returns:
        转录的文本
    """
    processor = AudioProcessor()
    return processor.transcribe(
        audio_file=audio_file,
        audio_bytes=audio_bytes,
        audio_base64=audio_base64,
        language=language,
    )


def synthesize_speech(
    text: str,
    voice: Optional[str] = None,
    output_format: str = "mp3",
    as_base64: bool = False,
) -> Union[bytes, str]:
    """
    文字转语音的便捷函数
    
    Args:
        text: 要转换的文本
        voice: 声音类型
        output_format: 输出格式
        as_base64: 是否返回 Base64 编码
    
    Returns:
        音频数据（bytes 或 base64 字符串）
    """
    processor = AudioProcessor()
    
    if as_base64:
        return processor.synthesize_to_base64(text, voice, output_format)
    else:
        return processor.synthesize(text, voice, output_format)
