import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\code\aicareer-assistant\backend\app\api\resume.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix known corrupted patterns
fixes = [
    ('PDF/Word\u2026)', 'PDF/Word)'),
    ('\u2026)\n', ')\n'),
]

for old, new in fixes:
    content = content.replace(old, new)

# Fix all lines with odd number of quotes (unterminated strings)
lines = content.split('\n')
fixed = 0
for i, line in enumerate(lines):
    # Count unescaped quotes
    quote_count = 0
    escape = False
    for ch in line:
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            quote_count += 1
    if quote_count % 2 == 1:
        # Line has odd number of quotes - try to fix
        # If line ends with ... or \u2026, close the string
        stripped = line.rstrip()
        if stripped.endswith('\u2026') or stripped.endswith('...'):
            lines[i] = stripped + '"'
            fixed += 1
            print(f'Fixed line {i+1}: closed unterminated string')
        elif '\u2026' in line and not stripped.endswith('"'):
            lines[i] = stripped + '"'
            fixed += 1
            print(f'Fixed line {i+1}: closed after ellipsis')

content = '\n'.join(lines)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Total fixes: {fixed}')
