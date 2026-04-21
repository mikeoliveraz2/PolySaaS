"""Crop to actual content bounding box, add even padding, re-upload."""
import requests, sys, io
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageChops

AZURE = "https://azure-nightingale-589250.hostingersite.com"
ORIG_URL = f"{AZURE}/wp-content/uploads/2026/03/dynamic-orchestration-request-path.png"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Download original RGBA
r = requests.get(ORIG_URL)
img = Image.open(io.BytesIO(r.content))
print(f"Original: {img.size}, mode: {img.mode}")

# Flatten alpha onto white
bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
bg.paste(img, mask=img.split()[3])
flat = bg.convert('RGB')

# Find bounding box of actual content (non-white pixels)
white_bg = Image.new('RGB', flat.size, (255, 255, 255))
diff = ImageChops.difference(flat, white_bg)
bbox = diff.getbbox()
print(f"Content bounding box: {bbox}")  # (left, top, right, bottom)

if bbox:
    content = flat.crop(bbox)
    print(f"Content size: {content.size}")
    
    # Add even padding on all sides
    pad = 30
    new_w = content.size[0] + pad * 2
    new_h = content.size[1] + pad * 2
    
    final = Image.new('RGB', (new_w, new_h), (255, 255, 255))
    final.paste(content, (pad, pad))
    print(f"Final with even padding: {final.size}")
    
    local_path = r"d:\PolySaaS\request-path-centered.png"
    final.save(local_path, "PNG")
    
    # Upload
    print("Uploading centered version...")
    with open(local_path, 'rb') as f:
        r2 = s.post(
            f"{AZURE}/wp-json/wp/v2/media",
            headers={"Content-Disposition": "attachment; filename=request-path-centered.png"},
            files={"file": ("request-path-centered.png", f, "image/png")},
        )
    
    if r2.status_code == 201:
        new_url = r2.json()['source_url']
        print(f"Uploaded: ID={r2.json()['id']}, URL={new_url}")
        
        # Update page
        r3 = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
        page = r3.json()[0]
        content_raw = page['content']['raw']
        
        # Find and replace the entire block
        import re
        old_url_pattern = r'https://azure-nightingale-589250\.hostingersite\.com/wp-content/uploads/2026/03/request-path-[^"]*\.png'
        new_content = re.sub(old_url_pattern, new_url, content_raw)
        
        if new_content != content_raw:
            r4 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page['id']}", json={"content": new_content})
            print(f"Page update: {r4.status_code}")
        else:
            print("No URL match found for replacement!")
    else:
        print(f"Upload failed: {r2.status_code}")
else:
    print("Could not detect content bounding box!")
