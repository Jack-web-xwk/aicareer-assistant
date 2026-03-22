"""
Learning - 学无止境专栏

学习阶段与文章数据模型。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

class LearningPhase(Base):
    """学习阶段（如前置准备、阶段一～六、番外篇）"""

    __tablename__ = "learning_phases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(128), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    articles: Mapped[list["LearningArticle"]] = relationship(
        "LearningArticle",
        back_populates="phase",
        order_by="LearningArticle.sort_order",
        cascade="all, delete-orphan",
    )


class LearningArticle(Base):
    """学习文章"""

    __tablename__ = "learning_articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    phase_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("learning_phases.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    content_md: Mapped[str] = mapped_column(Text, default="")
    external_url: Mapped[str] = mapped_column(String(1024), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    phase: Mapped["LearningPhase"] = relationship(
        "LearningPhase",
        back_populates="articles",
    )
