"""
Upload Monitor Logger screenshot and add to Monitor Logger detail page.
Then finish bingo: document, commit, push.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

img_path = r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_Monitor_Logger_Uptrace-6c0f87c7-f27b-4231-8583-13c43cc30ee2.png"
with open(img_path, 'rb') as f:
    data = f.read()
r = s.post(f"{AZURE}/wp-json/wp/v2/media",
    headers={"Content-Disposition": 'attachment; filename="monitor-logger-uptrace.png"', "Content-Type": "image/png"},
    data=data)
if r.status_code == 201:
    url = r.json()['source_url']
    print(f"Uploaded: {url}")
else:
    print(f"Upload failed: {r.status_code}")
    sys.exit(1)

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "monitor-logger-4", "context": "edit", "_fields": "id,content"
}).json()
page = pages[0]
raw = page['content']['raw']

img_block = f'''<div style="text-align:center;margin:20px auto;">
<img src="{url}" alt="Monitor Logger - Uptrace Log Viewer" style="width:100%;max-width:800px;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="color:var(--ps-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">Monitor Logger — real-time log aggregation with search, filtering, time-series visualization, and span-level detail</p>
</div>'''

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
print(f"Update Monitor Logger page: {r2.status_code}")
