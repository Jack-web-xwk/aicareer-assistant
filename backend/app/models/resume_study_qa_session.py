"""
Resume study QA session - 学习问答生成记录（持久化）
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .resume import Resume
    from .user import User


class ResumeStudyQaSession(Base):
    """单次「生成学习问答」的结果，关联一份已优化简历。"""

    __tablename__ = "resume_study_qa_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    resume_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
    )
    items_json: Mapped[str] = mapped_column(Text)
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    user: Mapped["User"] = relationship("User", back_populates="study_qa_sessions")
    resume: Mapped["Resume"] = relationship("Resume", back_populates="study_qa_sessions")
