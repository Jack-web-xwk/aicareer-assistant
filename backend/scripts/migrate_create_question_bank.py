"""
数据库迁移脚本 - 题库管理系统

创建 question_bank 表用于存储面试题目。

使用方法：
    python scripts/migrate_create_question_bank.py upgrade
    python scripts/migrate_create_question_bank.py downgrade
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_database_url() -> str:
    """获取数据库连接 URL（使用同步驱动进行迁移）"""
    url = settings.DATABASE_URL
    # 将 aiosqlite 转换为 sqlite3 用于迁移脚本
    if "aiosqlite" in url:
        url = url.replace("sqlite+aiosqlite", "sqlite")
    return url


def check_table_exists(engine, table_name: str) -> bool:
    """检查表是否已存在"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def check_index_exists(engine, table_name: str, index_name: str) -> bool:
    """检查索引是否已存在"""
    inspector = inspect(engine)
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def upgrade():
    """执行升级迁移"""
    logger.info("开始执行数据库迁移：创建题库表")
    
    engine = create_engine(get_database_url())
    
    try:
        with engine.connect() as conn:
            # 检查表是否已存在
            if check_table_exists(engine, "question_bank"):
                logger.warning("⚠️  question_bank 表已存在，跳过创建")
                return
            
            logger.info("创建 question_bank 表...")
            
            # 创建题库表
            conn.execute(text("""
                CREATE TABLE question_bank (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category VARCHAR(100) NOT NULL,
                    tech_stack TEXT,
                    difficulty VARCHAR(20) NOT NULL DEFAULT 'medium',
                    question TEXT NOT NULL,
                    expected_points TEXT,
                    follow_up_questions TEXT,
                    usage_count INTEGER NOT NULL DEFAULT 0,
                    avg_score FLOAT,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            logger.info("✓ question_bank 表创建成功")
            
            # 创建索引
            logger.info("创建索引...")
            
            # category 索引
            conn.execute(text("CREATE INDEX ix_category ON question_bank(category)"))
            logger.info("✓ ix_category 索引创建成功")
            
            # difficulty 索引
            conn.execute(text("CREATE INDEX ix_difficulty ON question_bank(difficulty)"))
            logger.info("✓ ix_difficulty 索引创建成功")
            
            # 组合索引：category + difficulty
            conn.execute(text("CREATE INDEX ix_category_difficulty ON question_bank(category, difficulty)"))
            logger.info("✓ ix_category_difficulty 索引创建成功")
            
            # 组合索引：category + is_active
            conn.execute(text("CREATE INDEX ix_category_active ON question_bank(category, is_active)"))
            logger.info("✓ ix_category_active 索引创建成功")
            
            conn.commit()
            
        logger.info("✅ 数据库迁移完成！")
        logger.info("创建表:")
        logger.info("  - question_bank: 题库存储表")
        logger.info("字段说明:")
        logger.info("  - id: 主键")
        logger.info("  - category: 分类名称（如'后端开发'、'前端开发'）")
        logger.info("  - tech_stack: 技术栈列表（JSON 格式）")
        logger.info("  - difficulty: 难度级别（easy/medium/hard）")
        logger.info("  - question: 问题描述")
        logger.info("  - expected_points: 期望回答要点（JSON 格式）")
        logger.info("  - follow_up_questions: 追问问题列表（JSON 格式）")
        logger.info("  - usage_count: 使用次数")
        logger.info("  - avg_score: 平均得分（0-100）")
        logger.info("  - is_active: 是否启用（软删除标记）")
        logger.info("  - created_at: 创建时间")
        logger.info("  - updated_at: 更新时间")
        
    except Exception as e:
        logger.error(f"❌ 迁移失败：{str(e)}", exc_info=True)
        raise
    finally:
        engine.dispose()


def downgrade():
    """执行降级迁移（回滚）"""
    logger.info("开始回滚数据库迁移：删除题库表")
    
    engine = create_engine(get_database_url())
    
    try:
        with engine.connect() as conn:
            # 检查表是否存在
            if not check_table_exists(engine, "question_bank"):
                logger.warning("⚠️  question_bank 表不存在，无需回滚")
                return
            
            logger.info("删除 question_bank 表...")
            conn.execute(text("DROP TABLE IF EXISTS question_bank"))
            logger.info("✓ question_bank 表删除成功")
            
            conn.commit()
            
        logger.info("✅ 数据库回滚完成！")
        
    except Exception as e:
        logger.error(f"❌ 回滚失败：{str(e)}", exc_info=True)
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python scripts/migrate_create_question_bank.py upgrade   # 执行升级")
        print("  python scripts/migrate_create_question_bank.py downgrade # 执行回滚")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "upgrade":
        upgrade()
    elif command == "downgrade":
        downgrade()
    else:
        print(f"未知命令：{command}")
        print("请使用 'upgrade' 或 'downgrade'")
        sys.exit(1)
