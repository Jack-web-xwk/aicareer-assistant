"""
Services - 业务服务层

包含简历解析、岗位爬取、音频处理等核心业务逻辑。
"""

from .resume_parser import ResumeParser, parse_resume_file
from .job_scraper import JobScraper, scrape_job_info
from .audio_processor import AudioProcessor, transcribe_audio, synthesize_speech

__all__ = [
    # Resume parsing
    "ResumeParser",
    "parse_resume_file",
    # Job scraping
    "JobScraper",
    "scrape_job_info",
    # Audio processing
    "AudioProcessor",
    "transcribe_audio",
    "synthesize_speech",
]
