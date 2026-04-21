"""Fix Request Path image — handle transparency properly, crop bottom, add right padding."""
import requests, sys, io
sys.stdout.reconfigure(encoding='utf-8')

from PIL import Image

AZURE = "https://azure-nightingale-589250.hostingersite.com"
# Use the ORIGINAL image, not the broken re-upload
ORIG_URL = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/dynamic-orchestration-request-path.png"

s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Download original
print("Downloading original image...")
r = requests.get(ORIG_URL)
img = Image.open(io.BytesIO(r.content))
print(f"Original: {img.size}, mode: {img.mode}")

# Handle transparency: flatten onto white background first
if img.mode in ('RGBA', 'LA', 'PA'):
    background = Image.new('RGB', img.size, (255, 255, 255))
    background.paste(img, mask=img.split()[-1])  # Use alpha as mask
    img = background
    print("Flattened transparency onto white background.")
elif img.mode != 'RGB':
    img = img.convert('RGB')
    print(f"Converted to RGB from {img.mode}")

w, h = img.size
print(f"Working size: {w}x{h}")

# Analyze: scan for the scrollbar at the bottom
# Check bottom rows for dark pixels that indicate scrollbar
for y in range(h-1, h-80, -1):
    row_pixels = [img.getpixel((x, y)) for x in range(w//4, 3*w//4, 10)]
    avg = tuple(sum(p[i] for p in row_pixels) // len(row_pixels) for i in range(3))
    is_dark = all(c < 100 for c in avg)
    is_white = all(c > 230 for c in avg)
    print(f"  Row {y}: avg={avg} {'DARK-bar' if is_dark else 'white' if is_white else 'content'}")
    if not is_dark and y < h - 5:
        crop_bottom = y + 5
        print(f"  -> Crop bottom at y={crop_bottom}")
        break
else:
    crop_bottom = h - 50

# Scan left edge for whitespace/transparency boundary  
for x in range(0, 100):
    col_pixels = [img.getpixel((x, y)) for y in range(h//4, 3*h//4, 10)]
    avg = tuple(sum(p[i] for p in col_pixels) // len(col_pixels) for i in range(3))
    has_content = any(c < 200 for c in avg)
    if has_content:
        crop_left = max(0, x - 10)
        print(f"  Content starts at x={x}, crop_left={crop_left}")
        break
else:
    crop_left = 0

# Crop
cropped = img.crop((crop_left, 0, w, crop_bottom))
print(f"Cropped: {cropped.size}")

# Add padding — especially on the right for the Chunk circle
pad = {"top": 10, "right": 40, "bottom": 15, "left": 10}
new_w = cropped.size[0] + pad["left"] + pad["right"]
new_h = cropped.size[1] + pad["top"] + pad["bottom"]

padded = Image.new('RGB', (new_w, new_h), (255, 255, 255))
padded.paste(cropped, (pad["left"], pad["top"]))
print(f"Padded: {padded.size}")

# Save
local_path = r"d:\PolySaaS\request-path-fixed2.png"
padded.save(local_path, "PNG", quality=95)
print(f"Saved: {local_path}")

# Upload
print("Uploading...")
with open(local_path, 'rb') as f:
    r2 = s.post(
        f"{AZURE}/wp-json/wp/v2/media",
        headers={"Content-Disposition": "attachment; filename=request-path-clean.png"},
        files={"file": ("request-path-clean.png", f, "image/png")},
    )

if r2.status_code == 201:
    media = r2.json()
    new_url = media['source_url']
    print(f"Uploaded: ID={media['id']}, URL={new_url}")
    
    # Update page — replace ALL references to old request-path images
    r3 = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
    page = r3.json()[0]
    content = page['content']['raw']
    
    # Replace any request-path image URL (original or previous fix)
    import re
    content_new = re.sub(
        r'https://azure-nightingale-589250\.hostingersite\.com/wp-content/uploads/2026/03/(dynamic-orchestration-request-path|request-path-graph)\.png',
        new_url,
        content
    )
    
    if content_new != content:
        r4 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page['id']}", json={"content": content_new})
        print(f"Page update: {r4.status_code}")
    else:
        print("No URL changes needed.")
else:
    print(f"Upload failed: {r2.status_code} {r2.text[:300]}")
