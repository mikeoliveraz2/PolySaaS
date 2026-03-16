"""Download the Request Path PNG, crop the scrollbar, add padding, re-upload."""
import requests, sys, io
sys.stdout.reconfigure(encoding='utf-8')

try:
    from PIL import Image
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'Pillow'])
    from PIL import Image

AZURE = "https://azure-nightingale-589250.hostingersite.com"
IMG_URL = f"{AZURE}/wp-content/uploads/2026/03/dynamic-orchestration-request-path.png"

s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Step 1: Download the original image
print("Downloading original image...")
r = requests.get(IMG_URL)
img = Image.open(io.BytesIO(r.content))
print(f"Original size: {img.size}")  # 1024x600

# Step 2: Analyze the image - find the scrollbar at the bottom
# The scrollbar is a dark horizontal bar in the bottom portion
# Let's crop it off and add clean padding
w, h = img.size

# Crop: remove bottom ~55px (scrollbar area) and left ~30px (whitespace)
# Keep right edge as-is (content goes to edge, we'll add padding)
crop_left = 20
crop_top = 0
crop_right = w
crop_bottom = h - 50  # Remove scrollbar bar at bottom

cropped = img.crop((crop_left, crop_top, crop_right, crop_bottom))
print(f"After crop: {cropped.size}")

# Step 3: Add clean padding around the content so nothing clips
pad_top = 15
pad_right = 35  # Extra room so Chunk circle isn't at the edge
pad_bottom = 20
pad_left = 15

new_w = cropped.size[0] + pad_left + pad_right
new_h = cropped.size[1] + pad_top + pad_bottom

# Create new image with white background
padded = Image.new('RGB', (new_w, new_h), (255, 255, 255))
padded.paste(cropped, (pad_left, pad_top))
print(f"After padding: {padded.size}")

# Step 4: Save locally
local_path = r"d:\PolySaaS\request-path-fixed.png"
padded.save(local_path, "PNG")
print(f"Saved to: {local_path}")

# Step 5: Upload to WordPress media library as a new file
print("Uploading to WordPress...")
with open(local_path, 'rb') as f:
    r2 = s.post(
        f"{AZURE}/wp-json/wp/v2/media",
        headers={"Content-Disposition": "attachment; filename=request-path-graph.png"},
        files={"file": ("request-path-graph.png", f, "image/png")},
    )

if r2.status_code == 201:
    media = r2.json()
    new_url = media['source_url']
    new_id = media['id']
    print(f"Uploaded! ID: {new_id}, URL: {new_url}")
    
    # Step 6: Update the page to use the new image
    r3 = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
    page = r3.json()[0]
    pid = page['id']
    content = page['content']['raw']
    
    # Replace old image URL with new one
    old_url = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/dynamic-orchestration-request-path.png"
    
    if old_url in content:
        new_content = content.replace(old_url, new_url)
        
        # Also simplify the container — no longer need the card wrapper since image is clean now
        old_block = '''<div style="text-align:center;margin:15px auto 25px;max-width:750px;">
<div style="background:#ffffff;border-radius:10px;padding:12px 16px 4px 8px;box-shadow:0 3px 15px rgba(0,0,0,0.15);overflow:hidden;">
<img src="''' + new_url + '''" alt="Request Path graph showing event-driven relationships" style="width:100%;height:auto;display:block;">
</div>
<p style="color:var(--ps-text-muted,#6B7280);font-size:0.85rem;margin-top:10px;font-style:italic;">Request Path graph: event-driven relationships across entities, categories, and locations</p>
</div>'''
        
        # Use same style as the working agent-flow image
        new_block = '''<div style="text-align:center;margin:15px auto 25px;max-width:700px;">
<img src="''' + new_url + '''" alt="Request Path graph showing event-driven relationships" style="width:100%;border-radius:10px;box-shadow:0 3px 12px rgba(0,0,0,0.1);">
<p style="color:var(--ps-text-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">Request Path graph: event-driven relationships across entities, categories, and locations</p>
</div>'''
        
        if old_block in new_content:
            new_content = new_content.replace(old_block, new_block)
            print("Replaced card wrapper with clean simple style (matching agent-flow).")
        else:
            # Just do the URL replacement
            print("Card wrapper pattern not found — just replacing URL.")
        
        r4 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
        print(f"Page update: {r4.status_code}")
        if r4.status_code == 200:
            print("DONE — New clean image uploaded and page updated.")
        else:
            print(f"Error: {r4.text[:300]}")
    else:
        print("Old URL not found in content!")
else:
    print(f"Upload failed: {r2.status_code}")
    print(r2.text[:500])
