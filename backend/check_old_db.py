import sqlite3

db_path = r"D:\code\aicareer-assistant\backend\scripts\data\career_assistant.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print(f"📊 检查数据库：{db_path}\n")

# 检查 interview_records
try:
    cursor.execute('SELECT COUNT(*) FROM interview_records')
    count = cursor.fetchone()[0]
    print(f"📝 面试记录数：{count}")
    
    if count > 0:
        cursor.execute("""
            SELECT id, job_role, company_name, created_at 
            FROM interview_records 
            ORDER BY created_at DESC
        """)
        records = cursor.fetchall()
        for r in records:
            print(f"  ID:{r[0]:4d} | {r[1]:20s} | {r[2] or '无公司':20s} | {r[3]}")
except Exception as e:
    print(f"❌ interview_records 查询失败：{e}")

print()

# 检查 resumes
try:
    cursor.execute('SELECT COUNT(*) FROM resumes')
    count = cursor.fetchone()[0]
    print(f"📄 简历记录数：{count}")
    
    if count > 0:
        cursor.execute("""
            SELECT id, original_filename, target_job_title, created_at 
            FROM resumes 
            ORDER BY created_at DESC
        """)
        records = cursor.fetchall()
        for r in records:
            print(f"  ID:{r[0]:4d} | {r[1]:30s} | {r[2] or '无岗位':20s} | {r[3]}")
except Exception as e:
    print(f"❌ resumes 查询失败：{e}")

conn.close()
