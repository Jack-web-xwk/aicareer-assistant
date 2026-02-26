"""
Database Initialization Script - 数据库初始化脚本

创建所有数据库表。
"""

import asyncio
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import create_tables, drop_tables, engine


async def init_database(drop_existing: bool = False):
    """
    初始化数据库
    
    Args:
        drop_existing: 是否删除现有表
    """
    print("🔧 Initializing database...")
    
    if drop_existing:
        print("⚠️  Dropping existing tables...")
        await drop_tables()
        print("✅ Existing tables dropped.")
    
    print("📝 Creating tables...")
    await create_tables()
    print("✅ Database tables created successfully!")
    
    # 关闭引擎
    await engine.dispose()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize the database")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop existing tables before creating new ones",
    )
    
    args = parser.parse_args()
    
    # 创建数据目录
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Data directory: {data_dir}")
    
    # 运行初始化
    asyncio.run(init_database(drop_existing=args.drop))
    
    print("\n✨ Database initialization complete!")
    print(f"📍 Database location: {data_dir / 'career_assistant.db'}")


if __name__ == "__main__":
    main()
