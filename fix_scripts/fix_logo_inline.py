"""Check how the logos currently render and fix to be inline with app name."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/2565",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# Show current h3 tags with logos
h3s = re.findall(r'<h3>(<img[^>]+>)([^<]+)</h3>', content)
print("=== Current h3 format ===")
for img, name in h3s[:3]:
    print(f"  {img[:80]}... {name.strip()}")

# The h3 might be displaying as block, causing logo to be on separate line
# Fix: ensure h3 displays as flex row with aligned items
# Also check the inv-card CSS
css_pos = content.find('.inv-card')
if css_pos > 0:
    # Get CSS around inv-card
    css_start = max(0, css_pos - 50)
    css_end = content.find('}', css_pos) + 1
    print(f"\n=== inv-card CSS ===")
    print(content[css_start:css_end+50])

# Find the inv-card h3 CSS
h3_css = content.find('.inv-card h3')
if h3_css > 0:
    end = content.find('}', h3_css) + 1
    print(f"\n=== inv-card h3 CSS ===")
    print(content[h3_css:end])

# The fix: add display:flex;align-items:center to the h3 tags
# This ensures logo and text are on the same line
app_names = ['Odoo', 'Nextcloud', 'Mattermost', 'WordPress', 'Liferay', 'Dolibarr', 'Monitor Logger', 'PolySysMon']

changes = 0
for name in app_names:
    old = f'<h3><img src="'
    # We need to target the specific h3 for each app
    pattern = f'<h3><img src="([^"]+)" alt="{name}" style="([^"]+)">{name}</h3>'
    match = re.search(pattern, content)
    if match:
        img_url = match.group(1)
        old_style = match.group(2)
        old_tag = match.group(0)
        new_tag = f'<h3 style="display:flex;align-items:center;gap:8px"><img src="{img_url}" alt="{name}" style="width:24px;height:24px;object-fit:contain;border-radius:4px;flex-shrink:0">{name}</h3>'
        content = content.replace(old_tag, new_tag)
        changes += 1

print(f"\nUpdated {changes} h3 tags")

if changes > 0:
    r2 = requests.post(BASE + "/wp-json/wp/v2/pages/2565",
                       auth=AUTH,
                       json={"content": content},
                       timeout=45)
    print(f"Update: {r2.status_code}")
    if r2.status_code == 200:
        print("SUCCESS - Logos now inline with app names using flexbox")
