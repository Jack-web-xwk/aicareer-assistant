"""
SQLite 数据库初始化脚本

快速初始化 SQLite 数据库，创建所有必要的表结构。
适合个人学习和开源项目使用。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import create_tables, engine
from app.core.config import settings
from app.utils.logger import get_logger
from sqlalchemy import text

logger = get_logger(__name__)


async def init_sqlite():
    """初始化 SQLite 数据库"""
    print("=" * 60)
    print("🚀 初始化 SQLite 数据库")
    print("=" * 60)
    print()
    
    # 显示当前配置
    print(f"📊 数据库类型：SQLite")
    print(f"📊 数据库路径：{settings.DATABASE_URL}")
    print()
    
    try:
        # 创建所有表
        print("📝 创建数据库表...")
        await create_tables()
        print("✅ 数据库表创建成功！")
        print()
        
        # 验证连接
        print("🔍 验证数据库连接...")
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"✅ 数据库连接正常")
        print()
        
        print("=" * 60)
        print("✨ SQLite 数据库初始化完成！")
        print("=" * 60)
        print()
        print("📋 下一步:")
        print("  1. 启动后端服务：python main.py")
        print("  2. 启动前端服务：cd frontend && npm run dev")
        print("  3. 访问应用：http://localhost:5173")
        print()
        print("💡 提示:")
        print("  - 数据库文件位置：backend/data/career_assistant.db")
        print("  - 备份数据库：复制 data 目录即可")
        print("  - 查看数据：sqlite3 backend/data/career_assistant.db")
        print()
        
    except Exception as e:
        print(f"❌ 初始化失败：{str(e)}")
        print()
        print("💡 请检查:")
        print("  1. data 目录是否存在：mkdir -p backend/data")
        print("  2. 文件权限是否正常")
        print("  3. 依赖是否已安装：pip install -r requirements.txt")
        print()
        raise


if __name__ == "__main__":
    asyncio.run(init_sqlite())
