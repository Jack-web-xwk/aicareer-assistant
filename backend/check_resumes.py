import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "data" / "career_assistant.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("📊 resumes 表结构:")
cursor.execute("PRAGMA table_info(resumes)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]:25s} | {col[2]:10s} | {'NOT NULL' if col[3] else 'NULL':8s}")

print("\n📝 resumes 表所有数据:")
cursor.execute("SELECT * FROM resumes")
rows = cursor.fetchall()
print(f"共 {len(rows)} 条记录\n")

for i, row in enumerate(rows, 1):
    print(f"--- 记录 {i} ---")
    for j, value in enumerate(row):
        print(f"  {columns[j][1]:25s}: {value}")
    print()

conn.close()
