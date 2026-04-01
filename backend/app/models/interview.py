"""
Interview Model - 面试记录模型

定义面试模拟记录数据表结构。
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, DateTime, Text, Integer, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .user import User


class InterviewStatus(str, Enum):
    """面试状态枚举"""
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"       # 已完成
    CANCELLED = "cancelled"       # 已取消


class InterviewRecord(Base):
    """
    面试记录模型
    
    存储用户的模拟面试记录和评估报告。
    """
    
    __tablename__ = "interview_records"
    
    # 主键
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 会话 ID（用于 WebSocket 连接识别）
    session_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    
    # 外键
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    
    # 面试配置
    job_role: Mapped[str] = mapped_column(String(255))  # 目标岗位
    tech_stack: Mapped[str] = mapped_column(Text)  # 技术栈（JSON array）
    difficulty_level: Mapped[str] = mapped_column(String(50), default="medium")  # easy/medium/hard
    
    # 关联的简历 ID（可选，用于从简历优化跳转）
    resume_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # 岗位详细信息（从简历或 saved_jobs 关联获取）
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # 公司名称
    salary_text: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 薪资范围
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # 工作地点
    job_description_full: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 完整 JD
    job_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 岗位快照 JSON
    
    # 对话记录
    conversation_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 评估结果
    total_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100
    strengths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    weaknesses: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    suggestions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    detailed_report: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Markdown
    
    # 多维度评估结果
    dimension_scores: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array - 5 维度详细评分
    realtime_feedback_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array - 实时反馈历史
    learning_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON - 个性化学习计划
    
    # 状态
    status: Mapped[InterviewStatus] = mapped_column(
        SQLEnum(InterviewStatus),
        default=InterviewStatus.IN_PROGRESS,
    )
    
    # 时间戳
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
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
    user: Mapped["User"] = relationship("User", back_populates="interview_records")
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """计算面试时长（分钟）"""
        if self.ended_at:
            delta = self.ended_at - self.started_at
            return delta.total_seconds() / 60
        return None
    
    def __repr__(self) -> str:
        return f"<InterviewRecord(id={self.id}, session={self.session_id}, role={self.job_role})>"
