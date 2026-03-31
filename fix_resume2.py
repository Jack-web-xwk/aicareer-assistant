import sys, re
sys.stdout.reconfigure(encoding='utf-8')

path = r'D:\code\aicareer-assistant\backend\app\api\resume.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Normalize line endings
content = content.replace('\r\n', '\n').replace('\r', '\n')
lines = content.split('\n')

fixed = 0
for i, line in enumerate(lines):
    stripped = line.rstrip('\n')
    
    # Skip empty lines and comments
    if not stripped.strip() or stripped.strip().startswith('#'):
        continue
    
    # Count quotes (rough)
    q_count = 0
    in_str = False
    for ch in stripped:
        if ch == '"':
            q_count += 1
    
    if q_count % 2 == 0:
        continue  # Even quotes, probably fine
    
    # Odd number of quotes - fix it
    # Strategy: if the line ends with ... or ... followed by ), add closing quote
    if stripped.endswith('...'):
        lines[i] = stripped + '"'
        fixed += 1
    elif re.search(r'\.\.\.\)$', stripped):
        lines[i] = re.sub(r'\.\.\.\)$', '...")', stripped)
        fixed += 1
    elif re.search(r'\.\.\.[^"]*$', stripped):
        # ... followed by non-quote stuff, add quote
        lines[i] = stripped + '"'
        fixed += 1
    else:
        # Generic: add closing quote before whatever's at the end
        lines[i] = stripped + '"'
        fixed += 1

result = '\n'.join(lines)

# Verify syntax iteratively (fix one error at a time)
max_passes = 20
for pass_num in range(max_passes):
    try:
        compile(result, 'resume.py', 'exec')
        print(f'Python syntax OK! Fixed {fixed} lines total ({pass_num+1} passes).')
        break
    except SyntaxError as e:
        prob_lines = result.split('\n')
        if e.lineno and e.lineno <= len(prob_lines):
            bad = prob_lines[e.lineno - 1]
            # Try to fix this specific line
            q = bad.count('"')
            if q % 2 == 1:
                if bad.rstrip().endswith('...'):
                    prob_lines[e.lineno - 1] = bad.rstrip() + '"'
                elif re.search(r'\.\.\.\)$', bad.rstrip()):
                    prob_lines[e.lineno - 1] = re.sub(r'\.\.\.\)$', '...")', bad.rstrip())
                else:
                    prob_lines[e.lineno - 1] = bad.rstrip() + '"'
                result = '\n'.join(prob_lines)
                fixed += 1
                print(f'Pass {pass_num+1}: Fixed line {e.lineno}')
            else:
                print(f'Pass {pass_num+1}: Line {e.lineno} has even quotes but still broken: {repr(bad[:80])}')
                break
        else:
            print(f'Pass {pass_num+1}: Unknown error at line {e.lineno}')
            break
else:
    print(f'Could not fully fix after {max_passes} passes.')

with open(path, 'w', encoding='utf-8') as f:
    f.write(result)
