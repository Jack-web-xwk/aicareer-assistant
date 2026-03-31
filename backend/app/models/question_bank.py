"""
Question Bank Model - 题库管理系统

定义面试题目数据表结构，支持 LLM+ 题库混合模式生成面试题。
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    String,
    DateTime,
    Text,
    Integer,
    Float,
    Boolean,
    Index,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.core.database import Base


class JSONType(TypeDecorator):
    """JSON 类型装饰器，用于存储 Python 字典/列表"""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Optional[Any], dialect) -> Optional[str]:
        """Python -> DB"""
        if value is None:
            return None
        import json

        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value: Optional[str], dialect) -> Optional[Any]:
        """DB -> Python"""
        if value is None:
            return None
        import json

        return json.loads(value)


class QuestionBank(Base):
    """
    题库存储模型

    存储面试题目，支持按分类、技术栈、难度级别筛选。
    与 LLM 生成模式配合使用，实现混合出题策略。
    """

    __tablename__ = "question_bank"

    # ==================== 基本信息 ====================
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 分类：如 "后端开发", "前端开发", "数据分析", "产品经理" 等
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    # 技术栈：JSON 数组，如 ["Python", "FastAPI", "SQLAlchemy"]
    tech_stack: Mapped[Optional[List[str]]] = mapped_column(JSONType, nullable=True)

    # 难度级别：easy/medium/hard
    difficulty: Mapped[str] = mapped_column(
        String(20), index=True, nullable=False, default="medium"
    )

    # ==================== 题目内容 ====================
    # 问题描述
    question: Mapped[str] = mapped_column(Text, nullable=False)

    # 期望回答要点：JSON 数组，用于评分参考
    expected_points: Mapped[Optional[List[str]]] = mapped_column(JSONType, nullable=True)

    # 追问问题列表：JSON 数组，用于深入考察
    follow_up_questions: Mapped[Optional[List[str]]] = mapped_column(
        JSONType, nullable=True
    )

    # ==================== 使用统计 ====================
    # 使用次数
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 平均得分（0-100）
    avg_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 是否启用（支持软删除）
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ==================== 时间戳 ====================
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # ==================== 索引 ====================
    __table_args__ = (
        # 组合索引：分类 + 难度
        Index("ix_category_difficulty", "category", "difficulty"),
        # 组合索引：分类 + 技术栈（部分数据库支持 JSON 索引）
        Index("ix_category_active", "category", "is_active"),
    )

    # ==================== 方法 ====================
    def increment_usage(self, score: Optional[float] = None) -> None:
        """
        增加使用次数，可选更新平均分

        Args:
            score: 本次使用的得分（可选）
        """
        self.usage_count += 1
        if score is not None:
            if self.avg_score is None:
                self.avg_score = score
            else:
                # 计算新的平均分
                total_score = self.avg_score * (self.usage_count - 1) + score
                self.avg_score = total_score / self.usage_count

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "category": self.category,
            "tech_stack": self.tech_stack or [],
            "difficulty": self.difficulty,
            "question": self.question,
            "expected_points": self.expected_points or [],
            "follow_up_questions": self.follow_up_questions or [],
            "usage_count": self.usage_count,
            "avg_score": self.avg_score,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<QuestionBank(id={self.id}, category='{self.category}', difficulty='{self.difficulty}')>"
