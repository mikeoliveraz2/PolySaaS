"""Check current state and fix the Request Path image once and for all."""
import requests, re, sys, io
sys.stdout.reconfigure(encoding='utf-8')

from PIL import Image

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Step 1: Check what the page currently has
r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']

# Find all request-path image references
for m in re.finditer(r'(request-path[^"\'>\s]*\.png)', content):
    print(f"Found reference: {m.group(1)}")

# Find the full img tag
img_match = re.search(r'<img[^>]*request-path[^>]*>', content)
if img_match:
    print(f"\nCurrent img tag:\n{img_match.group(0)}\n")

# Step 2: Download the ORIGINAL source image (the first one uploaded, RGBA)
ORIG_URL = f"{AZURE}/wp-content/uploads/2026/03/dynamic-orchestration-request-path.png"
print("Downloading original RGBA image...")
r_img = requests.get(ORIG_URL)
img = Image.open(io.BytesIO(r_img.content))
print(f"Original: {img.size}, mode: {img.mode}")

# Flatten alpha onto white
if img.mode in ('RGBA', 'LA', 'PA'):
    bg = Image.new('RGB', img.size, (255, 255, 255))
    bg.paste(img, mask=img.split()[-1])
    img = bg
elif img.mode != 'RGB':
    img = img.convert('RGB')

# Step 3: Add generous padding — especially on the right for Chunk
# Don't crop anything, just add padding to give breathing room
w, h = img.size
pad = {"top": 20, "right": 60, "bottom": 25, "left": 20}
new_w = w + pad["left"] + pad["right"]
new_h = h + pad["top"] + pad["bottom"]

padded = Image.new('RGB', (new_w, new_h), (255, 255, 255))
padded.paste(img, (pad["left"], pad["top"]))
print(f"Padded: {padded.size} (added {pad['right']}px right, {pad['bottom']}px bottom)")

local_path = r"d:\PolySaaS\request-path-v3.png"
padded.save(local_path, "PNG")

# Step 4: Upload
print("Uploading v3...")
with open(local_path, 'rb') as f:
    r2 = s.post(
        f"{AZURE}/wp-json/wp/v2/media",
        headers={"Content-Disposition": "attachment; filename=request-path-v3.png"},
        files={"file": ("request-path-v3.png", f, "image/png")},
    )

if r2.status_code != 201:
    print(f"Upload failed: {r2.status_code} {r2.text[:300]}")
    sys.exit(1)

new_url = r2.json()['source_url']
new_id = r2.json()['id']
print(f"Uploaded: ID={new_id}, URL={new_url}")

# Step 5: Find the entire wp:html block containing request-path and replace it completely
# Search for the block boundaries
rp_idx = content.find('request-path')
if rp_idx < 0:
    print("ERROR: Cannot find request-path in content!")
    sys.exit(1)

# Find the enclosing <!-- wp:html --> block
block_start = content.rfind('<!-- wp:html -->', 0, rp_idx)
block_end = content.find('<!-- /wp:html -->', rp_idx)
if block_end > 0:
    block_end += len('<!-- /wp:html -->')

old_block = content[block_start:block_end]
print(f"\nOld block:\n{old_block}\n")

# Build clean replacement — NO border-radius (it clips corners where Chunk is)
new_block = f'''<!-- wp:html -->
<div style="text-align:center;margin:15px auto 25px;max-width:700px;">
<img src="{new_url}" alt="Request Path graph showing event-driven relationships" style="width:100%;box-shadow:0 3px 12px rgba(0,0,0,0.1);">
<p style="color:var(--ps-text-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">Request Path graph: event-driven relationships across entities, categories, and locations</p>
</div>
<!-- /wp:html -->'''

new_content = content[:block_start] + new_block + content[block_end:]

r3 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Page update: {r3.status_code}")
if r3.status_code == 200:
    print("DONE — New clean image, no border-radius, 60px right padding in image.")
else:
    print(f"Error: {r3.text[:300]}")
