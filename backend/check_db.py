import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "data" / "career_assistant.db"

if not db_path.exists():
    print(f"❌ 数据库文件不存在：{db_path}")
    exit(1)

print(f"✅ 数据库文件：{db_path}")
print()

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 获取所有表
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
tables = cursor.fetchall()
print(f"📊 数据库表列表 ({len(tables)} 个):")
for table in tables:
    print(f"  - {table[0]}")

print()

# 检查 interview_records 表
try:
    cursor.execute('SELECT COUNT(*) FROM interview_records')
    count = cursor.fetchone()[0]
    print(f"📝 面试记录总数：{count}")
    
    if count > 0:
        print("\n📅 最近 10 条面试记录:")
        cursor.execute("""
            SELECT id, session_id, job_role, company_name, created_at 
            FROM interview_records 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        records = cursor.fetchall()
        for r in records:
            print(f"  ID:{r[0]:4d} | {r[2]:20s} | {r[3] or '无公司':20s} | {r[4]}")
    else:
        print("  (空表)")
except Exception as e:
    print(f"❌ 查询失败：{e}")

print()

# 检查 resumes 表
try:
    cursor.execute('SELECT COUNT(*) FROM resumes')
    count = cursor.fetchone()[0]
    print(f"📄 简历记录总数：{count}")
    
    if count > 0:
        print("\n📅 最近 10 份简历:")
        cursor.execute("""
            SELECT id, target_job_title, created_at 
            FROM resumes 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        records = cursor.fetchall()
        for r in records:
            job_title = str(r[1]) if r[1] else '无岗位'
            company_str = r[2] if r[2] else '无公司'
            created_at = r[3] if r[3] else '无时间'
            print(f"  ID:{r[0]:4d} | {job_title:20s} | {company_str:20s} | {created_at}")
    else:
        print("  (空表)")
except Exception as e:
    print(f"❌ 查询失败：{e}")

conn.close()
print()
print("✅ 检查完成！")
