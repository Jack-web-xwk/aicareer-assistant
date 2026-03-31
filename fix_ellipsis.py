import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\code\aicareer-assistant\backend\app\api\resume.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix all lines with broken preview += "...
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped == 'preview += "...':
        lines[i] = line.replace('preview += "...', 'preview += "\u2026"')
        print(f'Fixed line {i+1}: preview += "...')
    elif stripped.startswith('preview +=') and stripped.endswith('"...'):
        lines[i] = line.replace('"..."', '"\\u2026"')
        print(f'Fixed line {i+1}: {stripped}')

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Done')
