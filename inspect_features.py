"""Inspect the homepage feature blocks HTML structure."""
import requests, sys, json, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages/1313",
          params={"context": "edit", "_fields": "content"},
          timeout=30)
content = r.json()['content']['raw']

# Find the feature/platform section
# Look for "Platform Features" or the feature blocks
lines = content.split('\n')
in_features = False
feature_lines = []
for i, line in enumerate(lines):
    if 'Platform Features' in line or 'feature' in line.lower() or 'wp-block-columns' in line:
        in_features = True
    if in_features:
        feature_lines.append(f"{i}: {line}")
    if in_features and i > 0 and '</div>' in line and 'wp-block-columns' not in line:
        if len(feature_lines) > 50:
            break

# Let's just find all wp-block-columns occurrences
print("=== wp-block-columns occurrences ===")
for i, line in enumerate(lines):
    if 'wp-block-columns' in line:
        print(f"  Line {i}: {line[:200]}")

# Find the architecture section specifically
print("\n=== Looking for Architecture/Portal/feature blocks ===")
for i, line in enumerate(lines):
    if any(term in line for term in ['Architecture', 'Portal', 'Multi-Tenant', 'Enterprise', 'Real-Time', 'Analytics']):
        start = max(0, i-2)
        end = min(len(lines), i+3)
        for j in range(start, end):
            print(f"  Line {j}: {lines[j][:200]}")
        print("  ---")

# Check full content length
print(f"\nTotal content length: {len(content)} chars, {len(lines)} lines")

# Let's look for the actual feature section with more context
print("\n=== Feature section with context ===")
for i, line in enumerate(lines):
    if 'Platform Features' in line:
        start = max(0, i-5)
        end = min(len(lines), i+80)
        for j in range(start, end):
            print(f"  {j}: {lines[j][:250]}")
        break
