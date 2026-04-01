"""
数据库迁移脚本 - 为 interview_records 表添加岗位信息关联字段

新增字段：
- resume_id: 关联的简历 ID
- company_name: 公司名称
- salary_text: 薪资范围
- location: 工作地点
- job_description_full: 完整 JD
- job_snapshot: 岗位快照 JSON
"""

import asyncio
from sqlalchemy import text
from app.core.database import engine


async def migrate_add_interview_job_fields():
    """为 interview_records 表添加岗位信息字段"""
    async with engine.connect() as conn:
        try:
            print("🔧 正在为 interview_records 表添加字段...")
            
            # 添加 resume_id 字段
            try:
                await conn.execute(text("""
                    ALTER TABLE interview_records 
                    ADD COLUMN resume_id INTEGER
                """))
                await conn.commit()
                print("✅ 字段 resume_id 添加成功！")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print("✅ 字段 resume_id 已存在")
                    await conn.rollback()
                else:
                    raise
            
            # 添加 company_name 字段
            try:
                await conn.execute(text("""
                    ALTER TABLE interview_records 
                    ADD COLUMN company_name VARCHAR(255)
                """))
                await conn.commit()
                print("✅ 字段 company_name 添加成功！")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print("✅ 字段 company_name 已存在")
                    await conn.rollback()
                else:
                    raise
            
            # 添加 salary_text 字段
            try:
                await conn.execute(text("""
                    ALTER TABLE interview_records 
                    ADD COLUMN salary_text VARCHAR(100)
                """))
                await conn.commit()
                print("✅ 字段 salary_text 添加成功！")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print("✅ 字段 salary_text 已存在")
                    await conn.rollback()
                else:
                    raise
            
            # 添加 location 字段
            try:
                await conn.execute(text("""
                    ALTER TABLE interview_records 
                    ADD COLUMN location VARCHAR(255)
                """))
                await conn.commit()
                print("✅ 字段 location 添加成功！")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print("✅ 字段 location 已存在")
                    await conn.rollback()
                else:
                    raise
            
            # 添加 job_description_full 字段
            try:
                await conn.execute(text("""
                    ALTER TABLE interview_records 
                    ADD COLUMN job_description_full TEXT
                """))
                await conn.commit()
                print("✅ 字段 job_description_full 添加成功！")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print("✅ 字段 job_description_full 已存在")
                    await conn.rollback()
                else:
                    raise
            
            # 添加 job_snapshot 字段
            try:
                await conn.execute(text("""
                    ALTER TABLE interview_records 
                    ADD COLUMN job_snapshot TEXT
                """))
                await conn.commit()
                print("✅ 字段 job_snapshot 添加成功！")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print("✅ 字段 job_snapshot 已存在")
                    await conn.rollback()
                else:
                    raise
            
            # 为 resume_id 添加外键约束（SQLite 不支持动态添加外键，需要重建表）
            # 这里仅做标记，实际外键约束可以在后续通过完整迁移脚本实现
            print("ℹ️  注意：resume_id 的外键约束需要通过完整表重建来添加（SQLite 限制）")
            
            print("\n✅ 所有字段添加完成！")
            
        except Exception as e:
            print(f"\n❌ 迁移失败：{e}")
            await conn.rollback()
            raise


if __name__ == "__main__":
    print("🚀 开始执行数据库迁移...")
    asyncio.run(migrate_add_interview_job_fields())
    print("✨ 迁移完成！")
