"""
数据库迁移脚本 - 多维度评估系统

添加 interview_records 表的新字段：
- dimension_scores: JSON - 5 维度详细评分
- realtime_feedback_log: JSON - 实时反馈历史
- learning_plan: JSON - 个性化学习计划

使用方法：
    python scripts/migrate_add_assessment_fields.py upgrade
    python scripts/migrate_add_assessment_fields.py downgrade
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings
from app.core.database import Base
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_database_url(sync: bool = False) -> str:
    """获取数据库连接 URL
    
    Args:
        sync: 是否使用同步驱动（用于迁移脚本）
    """
    url = settings.DATABASE_URL
    if sync:
        # 将异步 SQLite 驱动转换为同步驱动
        url = url.replace("sqlite+aiosqlite://", "sqlite:///")
        # 确保使用绝对路径
        db_path = url.replace("sqlite:///", "")
        # 处理相对路径 (./data/... 或 data/...)
        if not os.path.isabs(db_path) or db_path.startswith('/.'):
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            # 移除开头的 ./ 或 /
            db_path = db_path.lstrip('./').lstrip('/')
            abs_path = os.path.join(base_dir, db_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            url = f"sqlite:///{abs_path}"
    return url


def check_column_exists(engine, table_name: str, column_name: str) -> bool:
    """检查列是否已存在"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    """执行升级迁移"""
    logger.info("开始执行数据库迁移：添加多维度评估字段")
    
    engine = create_engine(get_database_url(sync=True))
    
    try:
        with engine.connect() as conn:
            # 检查并添加 dimension_scores 列
            if not check_column_exists(engine, "interview_records", "dimension_scores"):
                logger.info("添加 dimension_scores 列...")
                conn.execute(text(
                    "ALTER TABLE interview_records "
                    "ADD COLUMN dimension_scores TEXT"
                ))
                logger.info("✓ dimension_scores 列添加成功")
            else:
                logger.info("- dimension_scores 列已存在，跳过")
            
            # 检查并添加 realtime_feedback_log 列
            if not check_column_exists(engine, "interview_records", "realtime_feedback_log"):
                logger.info("添加 realtime_feedback_log 列...")
                conn.execute(text(
                    "ALTER TABLE interview_records "
                    "ADD COLUMN realtime_feedback_log TEXT"
                ))
                logger.info("✓ realtime_feedback_log 列添加成功")
            else:
                logger.info("- realtime_feedback_log 列已存在，跳过")
            
            # 检查并添加 learning_plan 列
            if not check_column_exists(engine, "interview_records", "learning_plan"):
                logger.info("添加 learning_plan 列...")
                conn.execute(text(
                    "ALTER TABLE interview_records "
                    "ADD COLUMN learning_plan TEXT"
                ))
                logger.info("✓ learning_plan 列添加成功")
            else:
                logger.info("- learning_plan 列已存在，跳过")
            
            conn.commit()
            
        logger.info("✅ 数据库迁移完成！")
        logger.info("新增字段:")
        logger.info("  - dimension_scores: JSON 格式的 5 维度详细评分")
        logger.info("  - realtime_feedback_log: JSON 格式的实时反馈历史")
        logger.info("  - learning_plan: JSON 格式的个性化学习计划")
        
    except Exception as e:
        logger.error(f"❌ 迁移失败：{str(e)}", exc_info=True)
        raise
    finally:
        engine.dispose()


def downgrade():
    """执行降级迁移（回滚）"""
    logger.info("开始回滚数据库迁移：移除多维度评估字段")
    
    engine = create_engine(get_database_url(sync=True))
    
    try:
        with engine.connect() as conn:
            # 移除 learning_plan 列
            if check_column_exists(engine, "interview_records", "learning_plan"):
                logger.info("移除 learning_plan 列...")
                conn.execute(text(
                    "ALTER TABLE interview_records "
                    "DROP COLUMN learning_plan"
                ))
                logger.info("✓ learning_plan 列移除成功")
            else:
                logger.info("- learning_plan 列不存在，跳过")
            
            # 移除 realtime_feedback_log 列
            if check_column_exists(engine, "interview_records", "realtime_feedback_log"):
                logger.info("移除 realtime_feedback_log 列...")
                conn.execute(text(
                    "ALTER TABLE interview_records "
                    "DROP COLUMN realtime_feedback_log"
                ))
                logger.info("✓ realtime_feedback_log 列移除成功")
            else:
                logger.info("- realtime_feedback_log 列不存在，跳过")
            
            # 移除 dimension_scores 列
            if check_column_exists(engine, "interview_records", "dimension_scores"):
                logger.info("移除 dimension_scores 列...")
                conn.execute(text(
                    "ALTER TABLE interview_records "
                    "DROP COLUMN dimension_scores"
                ))
                logger.info("✓ dimension_scores 列移除成功")
            else:
                logger.info("- dimension_scores 列不存在，跳过")
            
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
        print("  python scripts/migrate_add_assessment_fields.py upgrade   # 执行升级")
        print("  python scripts/migrate_add_assessment_fields.py downgrade # 执行回滚")
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
