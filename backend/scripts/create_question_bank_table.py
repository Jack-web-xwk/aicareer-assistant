"""Simple script to create question_bank table"""
import sqlite3
import os

# 数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'data', 'career_assistant.db')
print(f"Database path: {db_path}")

# 连接数据库
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 检查表是否已存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='question_bank'")
    if cursor.fetchone():
        print("Table question_bank already exists, skipping...")
    else:
        # 创建题库表
        cursor.execute("""
            CREATE TABLE question_bank (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category VARCHAR(100) NOT NULL,
                tech_stack TEXT,
                difficulty VARCHAR(20) NOT NULL DEFAULT 'medium',
                question TEXT NOT NULL,
                expected_points TEXT,
                follow_up_questions TEXT,
                usage_count INTEGER NOT NULL DEFAULT 0,
                avg_score FLOAT,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("[OK] Table question_bank created successfully")
        
        # 创建索引
        cursor.execute("CREATE INDEX ix_category ON question_bank(category)")
        print("[OK] Index ix_category created")
        
        cursor.execute("CREATE INDEX ix_difficulty ON question_bank(difficulty)")
        print("[OK] Index ix_difficulty created")
        
        cursor.execute("CREATE INDEX ix_category_difficulty ON question_bank(category, difficulty)")
        print("[OK] Index ix_category_difficulty created")
        
        cursor.execute("CREATE INDEX ix_category_active ON question_bank(category, is_active)")
        print("[OK] Index ix_category_active created")
        
        conn.commit()
        print("\n[OK] Database migration completed successfully!")

except Exception as e:
    print(f"[ERROR] Error: {e}")
    raise
finally:
    conn.close()
