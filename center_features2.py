"""Check for any remaining uncentered feature rows and center them."""
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

features_start = raw.find('id="platform-features"')
features_end = raw.find('Stop Managing Tools')
section = raw[features_start:features_end]

# Find all wp-block-columns divs in section
cols = list(re.finditer(r'<div class="wp-block-columns[^"]*"[^>]*style="([^"]*)"', section))
print(f"Found {len(cols)} wp-block-columns rows in features section:")
changed = 0
for i, m in enumerate(cols):
    style = m.group(1)
    has_center = 'margin-left:auto' in style or 'max-width:900px' in style
    print(f"  {i+1}. {'CENTERED' if has_center else 'NOT centered'} — style=\"{style[:80]}\"")
    if not has_center:
        old_style_attr = f'style="{style}"'
        new_style = style.rstrip(';') + ';max-width:900px;margin-left:auto;margin-right:auto'
        new_style_attr = f'style="{new_style}"'
        section = section.replace(old_style_attr, new_style_attr, 1)
        changed += 1

if changed > 0:
    raw = raw[:features_start] + section + raw[features_end:]
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
                json={"content": raw}, timeout=30)
    print(f"\n  Centered {changed} additional rows. Status: {r2.status_code}")
else:
    print("\n  All rows already centered.")
