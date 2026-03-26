"""Center the Platform Features blocks on the homepage by adding
max-width and margin:auto to each wp-block-columns row in that section.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages",
          params={"slug": "home", "context": "edit", "_fields": "id,content"},
          timeout=30)
page = r.json()[0]
raw = page['content']['raw']
page_id = page['id']
print(f"Page ID: {page_id}, length: {len(raw)} chars")

features_start = raw.find('id="platform-features"')
features_end = raw.find('Stop Managing Tools')
if features_start < 0 or features_end < 0:
    print("ERROR: Could not find Platform Features section boundaries")
    sys.exit(1)

section = raw[features_start:features_end]
print(f"Section: {features_start}:{features_end} ({len(section)} chars)")

# Find all wp-block-columns rows in this section and add centering
# Pattern: style="margin-bottom:18px" on the columns div — add max-width and margin auto
old_style = 'style="margin-bottom:18px"'
new_style = 'style="margin-bottom:18px;max-width:900px;margin-left:auto;margin-right:auto"'

count = section.count(old_style)
print(f"Found {count} feature rows to center")

new_section = section.replace(old_style, new_style)
raw = raw[:features_start] + new_section + raw[features_end:]

# Also center the "Platform Features" heading itself if needed
# And the CTA section above it if present

print(f"\n=== Updating page (new length: {len(raw)} chars) ===")
r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
            json={"content": raw}, timeout=30)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    print(f"  SUCCESS! Centered {count} feature block rows (max-width:900px, margin:auto)")
else:
    print(f"  ERROR: {r2.text[:500]}")
