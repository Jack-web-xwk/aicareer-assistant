"""
题库管理系统简单测试
"""
import asyncio
import sys
import os
import pytest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, async_session_maker
from app.services.question_service import QuestionService


@pytest.mark.asyncio
async def test_question_service():
    """测试题库服务"""
    print("=" * 60)
    print("Testing Question Service")
    print("=" * 60)
    
    async with async_session_maker() as session:
        service = QuestionService(session)
        
        # 1. 测试统计
        print("\n[TEST 1] Getting statistics...")
        stats = await service.get_statistics()
        print(f"  Total questions: {stats['total_count']}")
        print(f"  Categories: {stats['category_stats']}")
        print(f"  Difficulties: {stats['difficulty_stats']}")
        
        # 2. 测试按分类查询（空题库）
        print("\n[TEST 2] Getting questions by category (expect empty)...")
        questions = await service.get_by_category(
            category="后端开发",
            difficulty="easy",
            limit=10
        )
        print(f"  Found {len(questions)} questions")
        
        # 3. 测试随机查询（空题库）
        print("\n[TEST 3] Getting random questions (expect empty)...")
        random_questions = await service.get_random_questions(limit=2)
        print(f"  Got {len(random_questions)} random questions")
        
        print("\n" + "=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_question_service())
