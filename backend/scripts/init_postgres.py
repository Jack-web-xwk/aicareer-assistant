"""
初始化 PostgreSQL 数据库

在本地开发环境中，使用 Docker 的 PostgreSQL 时运行此脚本。
创建所有必要的表结构。
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


async def init_database():
    """初始化数据库"""
    print("=" * 60)
    print("🚀 开始初始化 PostgreSQL 数据库")
    print("=" * 60)
    print()
    
    # 显示当前配置
    print(f"📊 数据库连接：{settings.DATABASE_URL}")
    print(f"📊 Redis 连接：{settings.REDIS_URL}")
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
            print(f"✅ 数据库连接正常：{result.scalar()}")
        print()
        
        print("=" * 60)
        print("✨ 数据库初始化完成！")
        print("=" * 60)
        print()
        print("📋 下一步:")
        print("  1. 启动后端服务：python main.py")
        print("  2. 启动前端服务：cd frontend && npm run dev")
        print("  3. 访问 http://localhost:5173")
        print()
        
    except Exception as e:
        print(f"❌ 初始化失败：{str(e)}")
        print()
        print("💡 请检查:")
        print("  1. Docker 容器是否运行：docker-compose ps")
        print("  2. PostgreSQL 是否可连接：docker-compose exec db psql -U careers -d aicareer -c 'SELECT 1'")
        print("  3. Redis 是否可连接：docker-compose exec redis redis-cli ping")
        print()
        raise


if __name__ == "__main__":
    asyncio.run(init_database())
