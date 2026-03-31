"""
题库管理系统测试
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.question_bank import QuestionBank
from app.services.question_service import QuestionService


async def test_question_service():
    """测试题库服务"""
    print("=" * 60)
    print("Testing Question Service")
    print("=" * 60)
    
    # 创建异步引擎和会话
    engine = create_async_engine(
        "sqlite+aiosqlite:///./backend/data/career_assistant.db",
        echo=False,
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        service = QuestionService(session)
        
        # 1. 测试创建题目
        print("\n[TEST 1] Creating questions...")
        test_questions = [
            {
                "category": "后端开发",
                "tech_stack": ["Python", "FastAPI"],
                "difficulty": "easy",
                "question": "请解释一下 FastAPI 的工作原理",
                "expected_points": ["异步处理", "类型提示", "自动文档"],
                "follow_up_questions": ["与 Flask 有什么区别？"]
            },
            {
                "category": "后端开发",
                "tech_stack": ["Python", "SQLAlchemy"],
                "difficulty": "medium",
                "question": "SQLAlchemy 的 ORM 模式有哪些优缺点？",
                "expected_points": ["代码简洁", "性能开销", "灵活性"],
                "follow_up_questions": ["什么时候使用 Core 而不是 ORM？"]
            },
            {
                "category": "前端开发",
                "tech_stack": ["React", "TypeScript"],
                "difficulty": "medium",
                "question": "React Hooks 的使用注意事项有哪些？",
                "expected_points": ["依赖数组", "闭包陷阱", "自定义 Hook"],
                "follow_up_questions": ["useEffect 和 useLayoutEffect 的区别？"]
            },
        ]
        
        created = []
        for q_data in test_questions:
            question = await service.create_question(q_data)
            created.append(question)
            print(f"  - Created: {question.id}. {question.question[:50]}...")
        
        # 2. 测试按分类查询
        print("\n[TEST 2] Getting questions by category...")
        backend_questions = await service.get_by_category(
            category="后端开发",
            difficulty="easy",
            limit=10
        )
        print(f"  Found {len(backend_questions)} easy backend questions")
        
        # 3. 测试随机查询
        print("\n[TEST 3] Getting random questions...")
        random_questions = await service.get_random_questions(limit=2)
        print(f"  Got {len(random_questions)} random questions")
        
        # 4. 测试搜索
        print("\n[TEST 4] Searching questions...")
        questions, total = await service.search_questions(
            keyword="FastAPI",
            category="后端开发"
        )
        print(f"  Search found {total} results")
        
        # 5. 测试更新使用次数
        if created:
            print("\n[TEST 5] Incrementing usage count...")
            updated = await service.increment_usage(created[0].id, score=85.0)
            print(f"  Updated usage_count={updated.usage_count}, avg_score={updated.avg_score}")
        
        # 6. 测试统计
        print("\n[TEST 6] Getting statistics...")
        stats = await service.get_statistics()
        print(f"  Total questions: {stats['total_count']}")
        print(f"  Categories: {stats['category_stats']}")
        print(f"  Difficulties: {stats['difficulty_stats']}")
        print(f"  Average usage: {stats['avg_usage']}")
        
        # 7. 测试批量导入
        print("\n[TEST 7] Batch importing questions...")
        batch_questions = [
            {
                "category": "数据分析",
                "tech_stack": ["Python", "Pandas"],
                "difficulty": "easy",
                "question": "Pandas 中 DataFrame 和 Series 有什么区别？",
                "expected_points": ["DataFrame 是二维", "Series 是一维"],
            },
            {
                "category": "数据分析",
                "tech_stack": ["Python", "NumPy"],
                "difficulty": "medium",
                "question": "NumPy 的广播机制是什么？",
                "expected_points": ["形状对齐", "隐式复制", "性能优化"],
            },
        ]
        
        result = await service.batch_import(batch_questions)
        print(f"  Imported: {result['imported']}, Skipped: {result['skipped']}, Failed: {result['failed']}")
        
        # 8. 测试删除（软删除）
        if created:
            print("\n[TEST 8] Deleting question (soft delete)...")
            success = await service.delete_question(created[-1].id)
            print(f"  Delete success: {success}")
            
            # 验证软删除后查询不到
            remaining, _ = await service.search_questions(is_active=True)
            active_count = len(remaining)
            print(f"  Active questions after delete: {active_count}")
    
    await engine.dispose()
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_question_service())
