"""
Upload second Liferay screenshot (portal dashboard) and add to Liferay page.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

img_path = r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_Liferay_Screen_shots_2-07d09dae-09ae-4019-98ff-ec67775b0561.png"
with open(img_path, 'rb') as f:
    data = f.read()
r = s.post(f"{AZURE}/wp-json/wp/v2/media",
    headers={"Content-Disposition": 'attachment; filename="liferay-portal-dashboard.png"', "Content-Type": "image/png"},
    data=data)
if r.status_code == 201:
    url = r.json()['source_url']
    print(f"Uploaded: {url}")
else:
    print(f"Upload failed: {r.status_code}")
    sys.exit(1)

# Add to Liferay page after the first screenshot
pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "liferay-2", "context": "edit", "_fields": "id,content"
}).json()
page = pages[0]
raw = page['content']['raw']

img_block = f'''<div style="text-align:center;margin:20px auto;">
<img src="{url}" alt="Liferay Portal Dashboard" style="width:100%;max-width:800px;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="color:var(--ps-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">Liferay Portal — enterprise content delivery with personalized dashboards and widget management</p>
</div>'''

# Insert after the first Liferay image (commerce screenshot)
first_img_idx = raw.find('liferay-commerce-screenshot')
if first_img_idx > 0:
    # Find end of that image block (closing </div> after the caption </p>)
    caption_end = raw.find('</p>', first_img_idx)
    if caption_end > 0:
        block_end = raw.find('</div>', caption_end) + 6
        new_raw = raw[:block_end] + "\n" + img_block + "\n" + raw[block_end:]
    else:
        # Fallback: insert before Key Capabilities
        key_cap = raw.find('Key Capabilities')
        new_raw = raw[:key_cap] + img_block + "\n" + raw[key_cap:]
else:
    # First image not found, insert before Key Capabilities
    key_cap = raw.find('Key Capabilities')
    insert = raw.rfind('<h2', max(0, key_cap-100), key_cap) if key_cap > 0 else -1
    if insert > 0:
        new_raw = raw[:insert] + img_block + "\n" + raw[insert:]
    else:
        print("Could not find insertion point")
        sys.exit(1)

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page['id']}", json={"content": new_raw})
print(f"Update Liferay page: {r2.status_code}")
