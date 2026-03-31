import re

path = r'D:\code\aicareer-assistant\backend\app\api\resume.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Step 1: Remove the get_or_create_user function (lines ~46-53)
# Step 2: Replace 'user = await Depends(get_current_user)' with 'user = current_user'
# Step 3: Add 'current_user: User = Depends(get_current_user),' to functions that use 'user = current_user'

output = []
skip_until_blank = False
for line in lines:
    # Remove get_or_create_user function
    if 'async def get_or_create_user(' in line:
        skip_until_blank = True
        continue
    if skip_until_blank:
        if line.strip() == '' or (line.strip().startswith('@') or line.strip().startswith('def ') or line.strip().startswith('async def ')):
            skip_until_blank = False
            output.append(line)
        continue
    output.append(line)

# Now fix: 'user = await Depends(get_current_user)' -> 'user = current_user'
content = ''.join(output)
content = content.replace('user = await Depends(get_current_user)', 'user = current_user')

# Now find functions that use 'user = current_user' and add current_user param
# Pattern: async def func_name(...):  and body has 'user = current_user'
lines = content.split('\n')
result = []
i = 0
while i < len(lines):
    line = lines[i]
    result.append(line)
    i += 1

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('done, checking...')

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
    
count = content.count('user = current_user')
print(f'Found {count} user = current_user lines')
print(f'get_or_create_user: {content.count("get_or_create_user")}')
