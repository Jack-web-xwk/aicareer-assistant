"""
User Model - 用户模型

定义用户数据表结构。
"""

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .resume import Resume
    from .interview import InterviewRecord
    from .saved_job import SavedJob
    from .resume_study_qa_session import ResumeStudyQaSession


class User(Base):
    """
    用户模型
    
    存储用户基本信息。
    """
    
    __tablename__ = "users"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 用户信息
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=True, index=True)
    avatar_url: Mapped[str] = mapped_column(String(512), nullable=True)
    
    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    
    # 关系
    resumes: Mapped[List["Resume"]] = relationship(
        "Resume",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    interview_records: Mapped[List["InterviewRecord"]] = relationship(
        "InterviewRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    saved_jobs: Mapped[List["SavedJob"]] = relationship(
        "SavedJob",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    study_qa_sessions: Mapped[List["ResumeStudyQaSession"]] = relationship(
        "ResumeStudyQaSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
