"""
Models - 数据模型

包含 SQLAlchemy ORM 模型和 Pydantic Schema 定义。
"""

from .user import User
from .resume import Resume
from .resume_study_qa_session import ResumeStudyQaSession
from .interview import InterviewRecord
from .saved_job import SavedJob
from .learning import LearningPhase, LearningArticle
from .question_bank import QuestionBank
from .schemas import (
    # User schemas
    UserCreate,
    UserResponse,
    # Resume schemas
    ResumeUploadRequest,
    ResumeOptimizeRequest,
    ResumeResponse,
    OptimizedResumeResponse,
    # Interview schemas
    InterviewStartRequest,
    InterviewMessageRequest,
    InterviewResponse,
    InterviewReportResponse,
    # Common schemas
    SuccessResponse,
    ErrorResponse,
)

__all__ = [
    # ORM Models
    "User",
    "Resume",
    "ResumeStudyQaSession",
    "InterviewRecord",
    "SavedJob",
    "LearningPhase",
    "LearningArticle",
    "QuestionBank",
    # User Schemas
    "UserCreate",
    "UserResponse",
    # Resume Schemas
    "ResumeUploadRequest",
    "ResumeOptimizeRequest",
    "ResumeResponse",
    "OptimizedResumeResponse",
    # Interview Schemas
    "InterviewStartRequest",
    "InterviewMessageRequest",
    "InterviewResponse",
    "InterviewReportResponse",
    # Common Schemas
    "SuccessResponse",
    "ErrorResponse",
]
