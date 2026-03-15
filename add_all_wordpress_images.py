"""
Upload 3 WordPress screenshots and add all to the WordPress detail page.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

IMAGES = [
    (r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_WordPress_Admin_Dashboard-e90636d3-1071-4677-a417-f4cf4e799d71.png",
     "wordpress-admin-dashboard.png", "WordPress Admin Dashboard", "WordPress admin dashboard — content management, site health, and quick actions at a glance"),
    (r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_wp_block_editor-c3700f3c-0f4d-4eb6-a9ab-146a6add410c.png",
     "wordpress-block-editor.png", "WordPress Block Editor", "WordPress Gutenberg block editor — visual page building with blocks, patterns, and full-site editing"),
    (r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_woordpress_block_editor_2-6f5c357d-3dc2-4bfc-95cf-b28c1fee10d5.png",
     "wordpress-block-editor-2.png", "WordPress Block Editor Interface", "Block editor in action — paragraph, image, heading, gallery, and list blocks at your fingertips"),
]

uploaded = []
for path, filename, alt, caption in IMAGES:
    with open(path, 'rb') as f:
        data = f.read()
    r = s.post(f"{AZURE}/wp-json/wp/v2/media",
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": "image/png"},
        data=data)
    if r.status_code == 201:
        url = r.json()['source_url']
        uploaded.append((url, alt, caption))
        print(f"Uploaded {filename}: {url}")
    else:
        print(f"Failed {filename}: {r.status_code}")

# Add all to WordPress page
pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "wordpress-3", "context": "edit", "_fields": "id,content"
}).json()
page = pages[0]
raw = page['content']['raw']

img_parts = []
for url, alt, caption in uploaded:
    img_parts.append(f'''<div style="text-align:center;margin:20px auto;">
<img src="{url}" alt="{alt}" style="width:100%;max-width:800px;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="color:var(--ps-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">{caption}</p>
</div>''')

img_block = "\n".join(img_parts)

key_cap_idx = raw.find('Key Capabilities')
if key_cap_idx > 0:
    insert_before = raw.rfind('<h2', max(0, key_cap_idx - 100), key_cap_idx)
    if insert_before < 0:
        insert_before = key_cap_idx
    new_raw = raw[:insert_before] + img_block + "\n" + raw[insert_before:]
else:
    subtitle_end = raw.find('</p>', raw.find('font-weight:500'))
    if subtitle_end > 0:
        new_raw = raw[:subtitle_end+4] + "\n" + img_block + "\n" + raw[subtitle_end+4:]
    else:
        print("Could not find insertion point")
        sys.exit(1)

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page['id']}", json={"content": new_raw})
print(f"Update WordPress page: {r2.status_code} ({len(uploaded)} images)")
