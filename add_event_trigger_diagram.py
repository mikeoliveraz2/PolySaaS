"""Upload and add the Request Path graph diagram after Event-Driven Triggers on Dynamic Orchestration page."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Upload the image
img_path = r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_dyn_orch1a-794fcd82-7d53-457a-bd3b-1debd09a964f.png"

with open(img_path, 'rb') as f:
    data = f.read()
print(f"Image size: {len(data)} bytes")

r = s.post(
    f"{AZURE}/wp-json/wp/v2/media",
    headers={
        "Content-Disposition": 'attachment; filename="dynamic-orchestration-request-path.png"',
        "Content-Type": "image/png",
    },
    data=data
)

if r.status_code == 201:
    media = r.json()
    img_url = media['source_url']
    print(f"Uploaded: id={media['id']}, url={img_url}")
    s.post(f"{AZURE}/wp-json/wp/v2/media/{media['id']}", json={
        "title": "Dynamic Orchestration — Request Path Graph",
        "alt_text": "Request Path graph showing event-driven relationships: competitors, investors, suppliers, categories, articles, cities, countries"
    })
else:
    print(f"Upload error: {r.status_code} {r.text[:200]}")
    exit(1)

# Now place it after Event-Driven Triggers on the page
r2 = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
page = r2.json()[0]
pid = page['id']
content = page['content']['raw']

# Find Event-Driven Triggers section
edt_idx = content.find('Event-Driven Triggers</h3>')
if edt_idx < 0:
    print("Event-Driven Triggers not found!")
    exit(1)

# Find the end of its description paragraph and card div
edt_para = content.find('</p>', edt_idx)
edt_div = content.find('</div>', edt_para)
insert_at = edt_div + len('</div>')

img_block = f'''
<!-- wp:html -->
<div style="text-align:center;margin:15px auto 25px;max-width:700px;">
<img src="{img_url}" alt="Request Path graph showing event-driven relationships" style="width:100%;border-radius:10px;box-shadow:0 3px 12px rgba(0,0,0,0.1);">
<p style="color:var(--ps-text-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">Request Path graph: event-driven relationships across entities, categories, and locations</p>
</div>
<!-- /wp:html -->'''

new_content = content[:insert_at] + img_block + content[insert_at:]

r3 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Update: {r3.status_code}")
if r3.status_code == 200:
    print("Done — Request Path diagram added after Event-Driven Triggers.")
else:
    print(f"Error: {r3.text[:300]}")
