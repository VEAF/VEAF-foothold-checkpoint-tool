#!/usr/bin/env python3
"""Fix missing closing parentheses for asyncio.run() calls"""

from pathlib import Path
import re

file_path = Path("tests/test_storage.py")
content = file_path.read_text(encoding="utf-8")

# Pattern: asyncio.run(function_name(...\n            )\n should be ...\n            ))\n
# We need to find places where asyncio.run( is followed by a function call that ends with just one )

# Find all asyncio.run(...) blocks and add closing paren
lines = content.split('\n')
new_lines = []
i = 0

fixes = 0

while i < len(lines):
    line = lines[i]
    
    # Check if line contains asyncio.run( and a function call
    if 'asyncio.run(' in line and any(f in line for f in ['save_checkpoint(', 'restore_checkpoint(', 'delete_checkpoint(', 'list_checkpoints(', 'import_checkpoint(', 'save_all_campaigns(']):
        # This line starts an asyncio.run call
        # Look ahead to find the closing )
        indent = len(line) - len(line.lstrip())
        j = i + 1
        paren_count = line.count('(') - line.count(')')
        
        # Find where this call ends
        while j < len(lines) and paren_count > 0:
            paren_count += lines[j].count('(') - lines[j].count(')')
            if paren_count == 1 and lines[j].strip() == ')':
                # This is the closing paren for the function, need to add one for asyncio.run
                new_lines.append(line)
                for k in range(i + 1, j):
                    new_lines.append(lines[k])
                new_lines.append(lines[j] + ')')
                fixes += 1
                i = j + 1
                break
            j += 1
        else:
            new_lines.append(line)
            i += 1
    else:
        new_lines.append(line)
        i += 1

content = '\n'.join(new_lines)
file_path.write_text(content, encoding="utf-8")

print(f"Fixed {fixes} missing closing parentheses")
