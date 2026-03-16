"""Download Apps As Peers image from production and add to Azure detail page."""
import requests, re, os

AZURE = "https://azure-nightingale-589250.hostingersite.com"
PROD = "https://polysaas.online"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

os.makedirs("temp_imgs", exist_ok=True)

# Download from production
prod_url = "https://polysaas.online/wp-content/uploads/2026/02/au-as-oers-1024x520.png"
print("Downloading from production...")
r = requests.get(prod_url, timeout=30)
if r.status_code != 200:
    # Try without the size suffix
    prod_url = "https://polysaas.online/wp-content/uploads/2026/02/au-as-oers.png"
    r = requests.get(prod_url, timeout=30)

if r.status_code == 200:
    filepath = "temp_imgs/apps-as-peers-diagram.png"
    with open(filepath, "wb") as f:
        f.write(r.content)
    print(f"Downloaded: {len(r.content)} bytes")
    
    # Upload to Azure
    print("Uploading to Azure...")
    with open(filepath, "rb") as f:
        data = f.read()
    
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/media",
        headers={
            "Content-Disposition": 'attachment; filename="apps-as-peers-diagram.png"',
            "Content-Type": "image/png"
        },
        data=data)
    
    if r2.status_code == 201:
        media = r2.json()
        img_url = media["source_url"]
        img_id = media["id"]
        print(f"Uploaded: id={img_id} url={img_url}")
    else:
        print(f"Upload failed: {r2.status_code} {r2.text[:300]}")
        # Check if already uploaded
        r_check = s.get(f"{AZURE}/wp-json/wp/v2/media", params={"search": "apps-as-peers-diagram"})
        existing = r_check.json()
        if existing:
            img_url = existing[0]["source_url"]
            img_id = existing[0]["id"]
            print(f"Already exists: id={img_id} url={img_url}")
        else:
            exit(1)
else:
    print(f"Download failed: {r.status_code}")
    exit(1)

# Now add to the Apps As Peers page
print("\nAdding to Apps As Peers page...")
r3 = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=apps-as-peers&context=edit")
page = r3.json()[0]
pid = page['id']
content = page['content']['raw']
print(f"Page id={pid}, content length={len(content)}")

# Check existing images
imgs = re.findall(r'<img[^>]+alt="([^"]*)"', content)
print(f"Current images: {imgs}")

# Build image HTML
image_html = '''
<div style="text-align:center;margin:20px auto;">
<img src="{url}" alt="Apps As Peers — applications communicating as equals" style="width:100%;max-width:900px;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="font-size:0.9rem;color:#666;margin-top:8px;font-style:italic;">Apps As Peers — bundled applications share data and trigger workflows as equal participants</p>
</div>
'''.format(url=img_url)

# Insert before Key Capabilities
key_cap = content.find('Key Capabilities')
if key_cap >= 0:
    h2_start = content.rfind('<h2', max(0, key_cap - 100), key_cap)
    if h2_start >= 0:
        insert_at = h2_start
    else:
        insert_at = key_cap - 10
    print(f"Inserting before 'Key Capabilities' at position {insert_at}")
else:
    # Fallback: after intro paragraph
    intro_end = content.find('</p>', content.find('Atomic Services'))
    insert_at = intro_end + 4 if intro_end >= 0 else len(content) // 3
    print(f"Fallback insertion at {insert_at}")

new_content = content[:insert_at] + image_html + content[insert_at:]

r4 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Update: {r4.status_code}")
if r4.status_code == 200:
    print("Done — Apps As Peers image added.")
else:
    print(f"Error: {r4.text[:300]}")
