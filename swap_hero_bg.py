"""Compress, upload, and swap in the server room hero background."""
import requests, re, sys, os
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Compress
src = r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\hero-bg-serverroom.png"
dst = r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\hero-bg-serverroom.jpg"
img = Image.open(src).convert("RGB")
img.save(dst, "JPEG", quality=75, optimize=True)
print(f"Original: {os.path.getsize(src)} bytes")
print(f"Compressed: {os.path.getsize(dst)} bytes")

# Upload
with open(dst, "rb") as f:
    img_data = f.read()

r1 = requests.post(
    BASE + "/wp-json/wp/v2/media",
    auth=AUTH,
    headers={
        "Content-Disposition": "attachment; filename=hero-bg-serverroom.jpg",
        "Content-Type": "image/jpeg",
    },
    data=img_data,
    timeout=60
)
print(f"Upload: {r1.status_code}")
if r1.status_code != 201:
    print(f"Error: {r1.text[:300]}")
    sys.exit(1)

new_url = r1.json()["source_url"]
print(f"New image URL: {new_url}")

# Swap in the homepage content
r2 = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                  params={"context": "edit", "_fields": "content"},
                  auth=AUTH, timeout=45)
content = r2.json()["content"]["raw"]

old_url = "https://polysaas.online/wp-content/uploads/2026/03/hero-bg-neural.jpg"
if old_url in content:
    content = content.replace(old_url, new_url)
    print(f"Swapped image URL ({content.count(new_url)} occurrences)")
else:
    print("Old URL not found!")
    sys.exit(1)

r3 = requests.post(BASE + "/wp-json/wp/v2/pages/1313",
                   auth=AUTH,
                   json={"content": content},
                   timeout=45)
print(f"Update: {r3.status_code}")
if r3.status_code == 200:
    print("SUCCESS - Server room background is now live")
else:
    print(f"Error: {r3.text[:300]}")
