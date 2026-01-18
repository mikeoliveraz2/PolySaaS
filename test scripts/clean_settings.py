#!/usr/bin/env python
"""
Clean settings.py file by removing any invalid content
"""
import re

# Read the file
with open('mysite/settings.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Remove any lines that contain date/time patterns that aren't comments
lines = content.split('\n')
cleaned_lines = []

for line in lines:
    # Skip lines that look like timestamps but aren't Python comments
    if re.match(r'^[A-Za-z]+,\s+[A-Za-z]+\s+\d+,\s+\d+\s+\d+:\d+:\d+\s+(AM|PM)$', line.strip()):
        print(f"Removing invalid line: {line.strip()}")
        continue
    cleaned_lines.append(line)

# Write back the cleaned content
with open('mysite/settings.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(cleaned_lines))

print("Settings file cleaned!")