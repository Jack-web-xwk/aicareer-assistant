"""Update interview_agent.py to add question bank integration"""
import re

# 读取文件
with open('backend/app/agents/interview_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 更新 docstring
old_docstring = '        """\n        节点 1: 初始化面试\n        \n        设置面试官角色，生成第一个技术问题。\n        """'
new_docstring = '        """\n        节点 1: 初始化面试\n        \n        设置面试官角色，生成第一个技术问题。\n        支持 LLM+ 题库混合模式：50% 概率从题库抽取，50% 概率 LLM 生成。\n        """'

if old_docstring in content:
    content = content.replace(old_docstring, new_docstring)
    print('1. Docstring updated successfully')
else:
    print('1. Old docstring not found')

# 写入文件
with open('backend/app/agents/interview_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("File updated successfully")
