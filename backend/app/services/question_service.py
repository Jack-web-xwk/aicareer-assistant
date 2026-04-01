"""
Question Service - 题库管理服务

提供题库相关的业务逻辑处理。
"""

import random
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, func, and_, or_, Text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.question_bank import QuestionBank
from app.utils.logger import get_logger

logger = get_logger(__name__)


class QuestionService:
    """
    题库服务类

    提供题库的 CRUD 操作、查询统计等功能。
    """

    def __init__(self, db: AsyncSession):
        """
        初始化服务

        Args:
            db: 异步数据库会话
        """
        self.db = db

    async def get_by_category(
        self,
        category: str,
        tech_stack: Optional[List[str]] = None,
        difficulty: Optional[str] = None,
        limit: int = 10,
    ) -> List[QuestionBank]:
        """
        按分类获取题目

        Args:
            category: 分类名称
            tech_stack: 技术栈过滤（支持多个）
            difficulty: 难度级别 (easy/medium/hard)
            limit: 返回数量限制

        Returns:
            题目列表
        """
        query = select(QuestionBank).where(
            and_(
                QuestionBank.category == category,
                QuestionBank.is_active == True,
            )
        )

        # 技术栈过滤：只要包含任一技术栈即可
        if tech_stack:
            # JSON 字段过滤，使用字符串匹配方式
            conditions = []
            for tech in tech_stack:
                conditions.append(
                    QuestionBank.tech_stack.cast(Text).like(f'%"{tech}"%')
                )
            query = query.where(or_(*conditions))

        # 难度过滤
        if difficulty:
            query = query.where(QuestionBank.difficulty == difficulty)

        # 按使用次数排序（优先使用少的），保证题目均匀分布
        query = query.order_by(QuestionBank.usage_count.asc(), QuestionBank.id.desc())
        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_random_questions(
        self,
        difficulty: Optional[str] = None,
        limit: int = 10,
    ) -> List[QuestionBank]:
        """
        随机获取题目

        Args:
            difficulty: 难度级别 (可选)
            limit: 返回数量限制

        Returns:
            随机题目列表
        """
        query = select(QuestionBank).where(QuestionBank.is_active == True)

        if difficulty:
            query = query.where(QuestionBank.difficulty == difficulty)

        # 随机排序
        query = query.order_by(func.random())
        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def increment_usage(
        self,
        question_id: int,
        score: Optional[float] = None,
    ) -> Optional[QuestionBank]:
        """
        增加题目使用次数

        Args:
            question_id: 题目 ID
            score: 本次得分（可选）

        Returns:
            更新后的题目，如果不存在则返回 None
        """
        query = select(QuestionBank).where(QuestionBank.id == question_id)
        result = await self.db.execute(query)
        question = result.scalar_one_or_none()

        if not question:
            logger.warning(f"题目不存在：id={question_id}")
            return None

        # 更新使用次数和平均分
        question.increment_usage(score)
        question.updated_at = func.now()

        await self.db.commit()
        await self.db.refresh(question)

        logger.info(f"题目使用次数已更新：id={question_id}, usage_count={question.usage_count}")
        return question

    async def search_questions(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        tech_stack: Optional[List[str]] = None,
        is_active: Optional[bool] = True,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[QuestionBank], int]:
        """
        搜索题目

        Args:
            keyword: 关键词（搜索问题描述）
            category: 分类
            difficulty: 难度
            tech_stack: 技术栈
            is_active: 是否只查询启用的题目
            offset: 偏移量
            limit: 数量限制

        Returns:
            (题目列表，总数)
        """
        # 构建基础查询
        conditions = []

        if is_active is not None:
            conditions.append(QuestionBank.is_active == is_active)

        if category:
            conditions.append(QuestionBank.category == category)

        if difficulty:
            conditions.append(QuestionBank.difficulty == difficulty)

        # 技术栈过滤
        if tech_stack:
            for tech in tech_stack:
                conditions.append(
                    QuestionBank.tech_stack.cast(Text).like(f'%"{tech}"%')
                )

        # 关键词搜索
        if keyword:
            conditions.append(QuestionBank.question.ilike(f"%{keyword}%"))

        # 查询总数
        count_query = select(func.count()).select_from(QuestionBank).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # 查询数据
        query = select(QuestionBank).where(and_(*conditions))
        query = query.order_by(QuestionBank.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        questions = list(result.scalars().all())

        return questions, total

    async def create_question(self, data: Dict[str, Any]) -> QuestionBank:
        """
        创建题目

        Args:
            data: 题目数据字典

        Returns:
            创建的题目对象
        """
        question = QuestionBank(**data)
        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)

        logger.info(f"题目已创建：id={question.id}, category={question.category}")
        return question

    async def update_question(
        self,
        question_id: int,
        data: Dict[str, Any],
    ) -> Optional[QuestionBank]:
        """
        更新题目

        Args:
            question_id: 题目 ID
            data: 更新数据

        Returns:
            更新后的题目，如果不存在则返回 None
        """
        query = select(QuestionBank).where(QuestionBank.id == question_id)
        result = await self.db.execute(query)
        question = result.scalar_one_or_none()

        if not question:
            logger.warning(f"题目不存在：id={question_id}")
            return None

        # 更新字段
        for key, value in data.items():
            if hasattr(question, key):
                setattr(question, key, value)

        question.updated_at = func.now()
        await self.db.commit()
        await self.db.refresh(question)

        logger.info(f"题目已更新：id={question_id}")
        return question

    async def delete_question(self, question_id: int) -> bool:
        """
        删除题目（软删除）

        Args:
            question_id: 题目 ID

        Returns:
            是否删除成功
        """
        query = select(QuestionBank).where(QuestionBank.id == question_id)
        result = await self.db.execute(query)
        question = result.scalar_one_or_none()

        if not question:
            logger.warning(f"题目不存在：id={question_id}")
            return False

        # 软删除：设置 is_active = False
        question.is_active = False
        question.updated_at = func.now()
        await self.db.commit()

        logger.info(f"题目已删除：id={question_id}")
        return True

    async def hard_delete_question(self, question_id: int) -> bool:
        """
        物理删除题目

        Args:
            question_id: 题目 ID

        Returns:
            是否删除成功
        """
        query = select(QuestionBank).where(QuestionBank.id == question_id)
        result = await self.db.execute(query)
        question = result.scalar_one_or_none()

        if not question:
            logger.warning(f"题目不存在：id={question_id}")
            return False

        await self.db.delete(question)
        await self.db.commit()

        logger.info(f"题目已物理删除：id={question_id}")
        return True

    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取题库统计数据

        Returns:
            统计数据字典
        """
        # 总题目数
        total_query = select(func.count()).where(QuestionBank.is_active == True)
        total_result = await self.db.execute(total_query)
        total_count = total_result.scalar() or 0

        # 按分类统计
        category_query = select(
            QuestionBank.category,
            func.count().label("count"),
        ).where(
            QuestionBank.is_active == True
        ).group_by(
            QuestionBank.category
        )
        category_result = await self.db.execute(category_query)
        category_stats = {row.category: row.count for row in category_result}

        # 按难度统计
        difficulty_query = select(
            QuestionBank.difficulty,
            func.count().label("count"),
        ).where(
            QuestionBank.is_active == True
        ).group_by(
            QuestionBank.difficulty
        )
        difficulty_result = await self.db.execute(difficulty_query)
        difficulty_stats = {row.difficulty: row.count for row in difficulty_result}

        # 平均使用次数
        avg_usage_query = select(
            func.avg(QuestionBank.usage_count)
        ).where(
            QuestionBank.is_active == True
        )
        avg_usage_result = await self.db.execute(avg_usage_query)
        avg_usage = avg_usage_result.scalar() or 0

        # 平均得分
        avg_score_query = select(
            func.avg(QuestionBank.avg_score)
        ).where(
            and_(
                QuestionBank.is_active == True,
                QuestionBank.avg_score.isnot(None),
            )
        )
        avg_score_result = await self.db.execute(avg_score_query)
        avg_score = avg_score_result.scalar() or 0

        # 最高使用次数的题目
        top_usage_query = select(QuestionBank).where(
            QuestionBank.is_active == True
        ).order_by(
            QuestionBank.usage_count.desc()
        ).limit(5)
        top_usage_result = await self.db.execute(top_usage_query)
        top_questions = [q.to_dict() for q in top_usage_result.scalars().all()]

        return {
            "total_count": total_count,
            "category_stats": category_stats,
            "difficulty_stats": difficulty_stats,
            "avg_usage": round(avg_usage, 2),
            "avg_score": round(avg_score, 2) if avg_score else None,
            "top_questions": top_questions,
        }

    async def batch_import(
        self,
        questions: List[Dict[str, Any]],
        skip_duplicates: bool = True,
    ) -> Dict[str, Any]:
        """
        批量导入题目

        Args:
            questions: 题目数据列表
            skip_duplicates: 是否跳过重复题目（根据 category+question 判断）

        Returns:
            导入结果统计
        """
        imported_count = 0
        skipped_count = 0
        failed_count = 0

        for q_data in questions:
            try:
                # 检查重复
                if skip_duplicates:
                    duplicate_query = select(QuestionBank).where(
                        and_(
                            QuestionBank.category == q_data.get("category"),
                            QuestionBank.question == q_data.get("question"),
                        )
                    )
                    duplicate_result = await self.db.execute(duplicate_query)
                    if duplicate_result.scalar_one_or_none():
                        skipped_count += 1
                        continue

                # 创建题目
                await self.create_question(q_data)
                imported_count += 1

            except Exception as e:
                logger.error(f"导入题目失败：{str(e)}", exc_info=True)
                failed_count += 1

        return {
            "imported": imported_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "total": len(questions),
        }

    async def get_question_by_id(self, question_id: int) -> Optional[QuestionBank]:
        """
        根据 ID 获取题目

        Args:
            question_id: 题目 ID

        Returns:
            题目对象，如果不存在则返回 None
        """
        query = select(QuestionBank).where(QuestionBank.id == question_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
