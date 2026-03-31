import re

with open('app/metrics/interview_metrics.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 删除所有 documentation 参数
content = re.sub(r",\s*documentation='[^']*'\)", ')', content)

with open('app/metrics/interview_metrics.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Fixed all documentation parameters')
