"""
Add Mattermost icon to the top of the Mattermost detail page.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")
MM_ICON = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/mattermost-icon.png"

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "mattermost", "context": "edit", "_fields": "id,content"
}).json()
mm = pages[0]
raw = mm['content']['raw']

# Find the first content block (after CSS/toggle blocks)
# Look for the first h1 or h2 or content div
blocks = re.findall(r'(<!-- wp:html -->.*?<!-- /wp:html -->)', raw, re.DOTALL)
print(f"Mattermost page: {len(blocks)} blocks, {len(raw)} chars")

# Find where the actual content starts (after CSS and toggle blocks)
content_start = 0
for b in blocks:
    if '<style' in b or 'ps-dark-toggle' in b or 'ps-theme-toggle' in b:
        end = raw.find(b) + len(b)
        if end > content_start:
            content_start = end

print(f"Content starts at: {content_start}")
print(f"Content preview: {raw[content_start:content_start+300]}")

# Insert the icon image after the CSS/toggle blocks, before the content
icon_block = f'''

<!-- wp:html -->
<div style="text-align:center;margin:16px auto 20px;">
<img src="{MM_ICON}" alt="Mattermost" style="width:120px;height:120px;object-fit:contain;border-radius:16px;">
</div>
<!-- /wp:html -->

'''

new_raw = raw[:content_start] + icon_block + raw[content_start:]

r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{mm['id']}", json={"content": new_raw})
print(f"Update: {r.status_code}")
if r.status_code == 200:
    print("Mattermost icon added to detail page")
