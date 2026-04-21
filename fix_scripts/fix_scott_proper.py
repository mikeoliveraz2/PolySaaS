"""
Properly fix Scott Chate's advisor card:
1. Remove the misplaced headshot insertion
2. Replace the SC placeholder circle with the actual headshot
3. Update his title
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")
SCOTT_URL = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/scott-chate-headshot.jpg"

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "about-us", "context": "edit", "_fields": "id,content"
}).json()
about = pages[0]
raw = about['content']['raw']

# Step 1: Remove the misplaced headshot div that was incorrectly inserted
# It looks like: <div style="text-align:center;..."><img src="...scott-chate-headshot..." ...></div>Scott Chate -->
misplaced = re.search(
    r'<div style="text-align:center;margin-bottom:8px;"><img src="[^"]*scott-chate-headshot[^"]*"[^>]*></div>',
    raw
)
if misplaced:
    print(f"Removing misplaced headshot ({len(misplaced.group())} chars)")
    raw = raw.replace(misplaced.group(), '')

# Step 2: Find the SC placeholder circle in Scott's card and replace with photo
# The placeholder: <div style="width:100px;height:100px;border-radius:50%;background:#E5E7EB;...">SC</div>
# We need to find the one that's in Scott's card specifically

# Find all advisor cards - look for the SC initials placeholder
sc_placeholder = re.search(
    r'<div style="width:100px;height:100px;border-radius:50%;background:#E5E7EB;[^"]*">SC</div>',
    raw
)
if sc_placeholder:
    old_ph = sc_placeholder.group()
    new_img = f'<img src="{SCOTT_URL}" alt="Scott Chate" style="width:100px;height:100px;border-radius:50%;object-fit:cover;margin:0 auto 12px auto;display:block;">'
    raw = raw.replace(old_ph, new_img, 1)
    print(f"Replaced SC placeholder with headshot")
else:
    print("SC placeholder not found")

# Step 3: Find and update Scott's title
# Look for his name heading and the role text after it
scott_card = re.search(
    r'(Scott Chate</h3>\s*<p[^>]*>)([^<]*)(</p>)',
    raw
)
if scott_card:
    old_title = scott_card.group(2)
    print(f"Current title: '{old_title}'")
    new_title = "VP Partner &amp; Market Development, Corent Technology, Inc"
    full_old = scott_card.group(0)
    full_new = scott_card.group(1) + new_title + scott_card.group(3)
    raw = raw.replace(full_old, full_new, 1)
    print(f"Updated title to: VP Partner & Market Development, Corent Technology, Inc")
else:
    # Try broader search
    scott_name_idx = raw.find('>Scott Chate</h3>')
    if scott_name_idx > 0:
        after = raw[scott_name_idx:scott_name_idx+300]
        print(f"After Scott's name h3: {after[:300]}")
    else:
        print("Could not find Scott Chate h3 heading")

r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{about['id']}", json={"content": raw})
print(f"\nUpdate: {r.status_code}")
if r.status_code == 200:
    print("Scott's card fixed: headshot + correct title")
