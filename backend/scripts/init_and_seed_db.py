"""
数据库初始化和种子数据脚本

修复数据库初始化问题，确保必要的数据被正确创建。
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent / '..'))

from sqlalchemy import select, func
from app.core.database import create_tables, ensure_sqlite_schema, async_session_maker
from app.models.user import User
from app.models.learning import LearningPhase, LearningArticle
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def create_default_user():
    """创建默认用户（如果不存在）"""
    async with async_session_maker() as db:
        result = await db.execute(select(User).where(User.email == "default@example.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            logger.info("创建默认用户...")
            user = User(
                email="default@example.com",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu",  # "password"
            )
            db.add(user)
            await db.commit()
            logger.info("✓ 默认用户创建成功 (email: default@example.com, password: password)")
        else:
            logger.info("✓ 默认用户已存在")


async def seed_learning_data():
    """播种学习数据（如果为空）"""
    from app.services.learning_seed import seed_learning_if_empty
    
    async with async_session_maker() as db:
        n = await seed_learning_if_empty(db)
        if n > 0:
            logger.info(f"✓ 学习数据播种完成，共 {n} 篇文章")
        else:
            logger.info("✓ 学习数据已存在")


async def verify_database():
    """验证数据库状态"""
    async with async_session_maker() as db:
        # 检查用户数
        result = await db.execute(select(func.count()).select_from(User))
        user_count = result.scalar_one() or 0
        logger.info(f"用户总数：{user_count}")
        
        # 检查学习阶段和文章数
        result = await db.execute(select(func.count()).select_from(LearningPhase))
        phase_count = result.scalar_one() or 0
        result = await db.execute(select(func.count()).select_from(LearningArticle))
        article_count = result.scalar_one() or 0
        logger.info(f"学习阶段数：{phase_count}, 文章数：{article_count}")
        
        # 检查题库数量
        from app.models.question_bank import QuestionBank
        result = await db.execute(select(func.count()).select_from(QuestionBank))
        question_count = result.scalar_one() or 0
        logger.info(f"题库数量：{question_count}")


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始数据库初始化和验证")
    logger.info("=" * 60)
    
    try:
        # 创建表结构
        logger.info("\n步骤 1: 创建数据库表...")
        await create_tables()
        logger.info("✓ 数据库表创建完成")
        
        # SQLite 特殊迁移
        logger.info("\n步骤 2: 执行 SQLite 迁移...")
        await ensure_sqlite_schema()
        logger.info("✓ SQLite 迁移完成")
        
        # 创建默认用户
        logger.info("\n步骤 3: 创建默认用户...")
        await create_default_user()
        
        # 播种学习数据
        logger.info("\n步骤 4: 播种学习数据...")
        await seed_learning_data()
        
        # 验证数据库
        logger.info("\n步骤 5: 验证数据库状态...")
        await verify_database()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 数据库初始化完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 初始化失败：{str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
