import sqlite3
import os

db_path = os.path.abspath('backend/data/career_assistant.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='question_bank'")
result = cursor.fetchone()
if result:
    print('Table question_bank exists!')
    
    # 获取表结构
    cursor.execute('PRAGMA table_info(question_bank)')
    columns = cursor.fetchall()
    print('\nColumns:')
    for col in columns:
        print(f'  - {col[1]} ({col[2]})')
    
    # 检查索引
    cursor.execute('PRAGMA index_list(question_bank)')
    indexes = cursor.fetchall()
    print('\nIndexes:')
    for idx in indexes:
        print(f'  - {idx[1]}')
else:
    print('Table not found!')

conn.close()
