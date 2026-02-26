"""
Resume Model - 简历模型

定义简历数据表结构。
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .user import User


class ResumeStatus(str, Enum):
    """简历状态枚举"""
    UPLOADED = "uploaded"      # 已上传
    PARSING = "parsing"        # 解析中
    PARSED = "parsed"          # 已解析
    OPTIMIZING = "optimizing"  # 优化中
    OPTIMIZED = "optimized"    # 已优化
    FAILED = "failed"          # 处理失败


class Resume(Base):
    """
    简历模型
    
    存储用户上传的简历和优化后的简历信息。
    """
    
    __tablename__ = "resumes"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 外键
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    
    # 原始文件信息
    original_filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(50))  # pdf, docx
    
    # 解析内容
    original_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    # 目标岗位
    target_job_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    target_job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    job_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 优化结果
    optimized_resume: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Markdown
    match_analysis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    # 状态
    status: Mapped[ResumeStatus] = mapped_column(
        SQLEnum(ResumeStatus),
        default=ResumeStatus.UPLOADED,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
    user: Mapped["User"] = relationship("User", back_populates="resumes")
    
    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, filename={self.original_filename}, status={self.status})>"
