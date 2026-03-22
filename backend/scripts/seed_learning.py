"""
Seed Learning Data - 学无止境专栏初始数据

按豆包《AI 大模型全栈工程师成长专栏》设计写入阶段与文章。
可手动运行：python scripts/seed_learning.py
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import async_session_maker, create_tables
from app.services.learning_seed import seed_learning_if_empty


async def main():
    print("[Seed] Seeding learning data...")
    await create_tables()
    async with async_session_maker() as session:
        count = await seed_learning_if_empty(session)
    print(f"[Seed] Done. Articles seeded: {count}")


if __name__ == "__main__":
    asyncio.run(main())
