"""
添加 Resume 模型的 langgraph_node_outputs 字段

用于持久化存储 LangGraph 节点执行数据，支持历史回看。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from sqlalchemy import text
from app.core.database import engine


async def migrate_add_langgraph_node_outputs_field():
    """添加 langgraph_node_outputs 字段"""
    async with engine.connect() as conn:
        try:
            # 直接添加字段，如果已存在会抛出异常，我们捕获即可
            print("🔧 正在添加 langgraph_node_outputs 字段...")
            await conn.execute(text("""
                ALTER TABLE resumes 
                ADD COLUMN langgraph_node_outputs TEXT
            """))
            await conn.commit()
            print("✅ 字段 langgraph_node_outputs 添加成功！")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("✅ 字段 langgraph_node_outputs 已存在")
                await conn.rollback()
            else:
                raise


def main():
    """主函数"""
    print("🚀 开始数据库迁移：添加 langgraph_node_outputs 字段")
    asyncio.run(migrate_add_langgraph_node_outputs_field())
    print("✨ 数据库迁移完成！")


if __name__ == "__main__":
    main()
