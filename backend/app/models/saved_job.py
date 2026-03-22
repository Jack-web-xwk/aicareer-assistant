"""
用户保存的职位（来自搜索聚合结果，持久化到数据库）。
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .user import User


class SavedJob(Base):
    """用户从职位搜索中保存的岗位条目。"""

    __tablename__ = "saved_jobs"
    __table_args__ = (
        UniqueConstraint("user_id", "detail_url", name="uq_saved_jobs_user_detail_url"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    title: Mapped[str] = mapped_column(String(500))
    company_name: Mapped[str] = mapped_column(String(300), default="")
    salary_text: Mapped[str] = mapped_column(String(200), default="")
    location: Mapped[str] = mapped_column(String(200), default="")
    published_at: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    experience_text: Mapped[str] = mapped_column(String(200), default="")
    education_text: Mapped[str] = mapped_column(String(200), default="")
    source: Mapped[str] = mapped_column(String(32), index=True)
    detail_url: Mapped[str] = mapped_column(String(1200))
    raw_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship("User", back_populates="saved_jobs")
