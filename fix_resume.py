import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\code\aicareer-assistant\backend\app\api\resume.py'

# Read as bytes
with open(path, 'rb') as f:
    data = f.read()

# The original file had Unicode ellipsis (U+2026) which got corrupted.
# Let's search for the exact byte pattern that breaks Python strings:
# Pattern: a quoted string followed by U+2026 then NO closing quote

# Strategy: decode with utf-8, find all lines with syntax issues, fix them
content = data.decode('utf-8', errors='replace')
lines = content.split('\n')

fixed = 0
for i, line in enumerate(lines):
    # Count quotes (rough but sufficient for our specific issue)
    # The problem: lines like: description="简历文件（PDF/Word...)
    # or: logger.info("开始XXX...)
    # These have UNTERMINATED strings because the ellipsis ate the closing quote
    
    # Fix pattern: if line has ... at the end of a string literal without closing quote
    import re
    
    # Pattern 1: "text...  where ... is at end without closing "
    # Look for lines ending with ... that are missing a closing quote
    m = re.search(r'"([^"]*)\.\.\.$', line.rstrip())
    if m:
        lines[i] = line.rstrip() + '"'
        fixed += 1
        continue
    
    # Pattern 2: ...  in middle of line with odd quotes
    # Specifically: description="...  or info("...
    stripped = line.strip()
    if '\u2026' in line:
        # Has Unicode ellipsis - replace with ...
        lines[i] = line.replace('\u2026', '...')
        # Check if now has odd quotes
        q = lines[i].count('"') - lines[i].count('\\"')
        if q % 2 == 1:
            # Add closing quote
            if lines[i].rstrip().endswith('...'):
                lines[i] = lines[i].rstrip() + '"'
            elif lines[i].rstrip().endswith(')'):
                # info("开始优化...") - need to add quote before )
                lines[i] = lines[i].rstrip()[:-1] + '")'
        fixed += 1

result = '\n'.join(lines)

# Verify syntax
try:
    compile(result, 'resume.py', 'exec')
    print(f'Python syntax OK! Fixed {fixed} lines.')
except SyntaxError as e:
    print(f'Still broken at line {e.lineno}: {e.msg}')
    print(f'Fixed so far: {fixed} lines.')
    # Show the problematic line
    prob_lines = result.split('\n')
    if e.lineno:
        print(f'Problematic line {e.lineno}: {repr(prob_lines[e.lineno-1])}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(result)
