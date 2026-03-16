"""Upload new Request Path image and update the page."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Upload the new image
img_path = r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_dyn_orch11b-40a016a4-4ed5-44ec-b775-c28a221841d7.png"

print("Uploading new Request Path image...")
with open(img_path, 'rb') as f:
    r = s.post(
        f"{AZURE}/wp-json/wp/v2/media",
        headers={"Content-Disposition": "attachment; filename=polysaas-middleware-graph.png"},
        files={"file": ("polysaas-middleware-graph.png", f, "image/png")},
    )

if r.status_code != 201:
    print(f"Upload failed: {r.status_code} {r.text[:300]}")
    sys.exit(1)

new_url = r.json()['source_url']
new_id = r.json()['id']
print(f"Uploaded: ID={new_id}, URL={new_url}")

# Update the page — find the request-path block and replace with new image
r2 = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
page = r2.json()[0]
pid = page['id']
content = page['content']['raw']

# Find the block containing request-path
rp_idx = content.find('request-path')
if rp_idx < 0:
    print("ERROR: Cannot find request-path in content!")
    sys.exit(1)

block_start = content.rfind('<!-- wp:html -->', 0, rp_idx)
block_end = content.find('<!-- /wp:html -->', rp_idx) + len('<!-- /wp:html -->')

old_block = content[block_start:block_end]
print(f"\nOld block:\n{old_block}\n")

# New block — same style as the working agent-flow image
new_block = f'''<!-- wp:html -->
<div style="text-align:center;margin:15px auto 25px;max-width:700px;">
<img src="{new_url}" alt="PolySaaS Middleware — event-driven relationships across entities" style="width:100%;border-radius:10px;box-shadow:0 3px 12px rgba(0,0,0,0.1);">
<p style="color:var(--ps-text-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">PolySaaS Middleware graph: event-driven relationships across entities, categories, and locations</p>
</div>
<!-- /wp:html -->'''

new_content = content[:block_start] + new_block + content[block_end:]

r3 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Page update: {r3.status_code}")
if r3.status_code == 200:
    print("DONE — New clean image uploaded and placed.")
else:
    print(f"Error: {r3.text[:300]}")
