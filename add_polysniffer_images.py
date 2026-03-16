"""Add PolySniffer Capture and PassThrough endpoint images to the PolySniffer detail page."""
import requests, re

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# The two images to add
PASSTHROUGH_IMG = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/02/Select-pass-through-endpoint-to-change-D-O-S-E-Administration-02-24-2026_12_08_PM-Start-PolySniffer-scaled.png"
CAPTURE_IMG = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/02/PolySniffer-Live-Capture-Nextcloud-02-24-2026_12_06_PM-via-polysniffer-2-scaled.png"

# Get PolySniffer page
r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=polysniffer&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']
print(f"PolySniffer page id={pid}, content length={len(content)}")

# Find existing images
imgs = list(re.finditer(r'<img[^>]+>', content))
print(f"Current images: {len(imgs)}")
for i, m in enumerate(imgs):
    alt = re.search(r'alt="([^"]*)"', m.group())
    alt_val = alt.group(1) if alt else "no alt"
    print(f"  [{i}] {alt_val}")

# Build the image HTML blocks
images_html = '''
<div style="text-align:center;margin:20px auto;">
<img src="{passthrough}" alt="PassThrough Endpoints — PolySniffer link" style="width:100%;max-width:900px;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="font-size:0.9rem;color:#666;margin-top:8px;font-style:italic;">PassThrough Endpoints with PolySniffer link — launch PolySniffer directly from endpoint configuration</p>
</div>

<div style="text-align:center;margin:20px auto;">
<img src="{capture}" alt="PolySniffer Live Capture Screen" style="width:100%;max-width:900px;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="font-size:0.9rem;color:#666;margin-top:8px;font-style:italic;">PolySniffer Live Capture — real-time protocol, cookie, and header inspection</p>
</div>
'''.format(passthrough=PASSTHROUGH_IMG, capture=CAPTURE_IMG)

# Find the best insertion point: after the intro text, before "Key Capabilities"
key_cap = content.find('Key Capabilities')
if key_cap >= 0:
    # Find the H2 tag containing it
    h2_start = content.rfind('<h2', max(0, key_cap - 100), key_cap)
    if h2_start >= 0:
        insert_at = h2_start
        print(f"\nInserting images before 'Key Capabilities' at position {insert_at}")
    else:
        insert_at = key_cap - 10
        print(f"\nInserting before Key Capabilities text at {insert_at}")
else:
    # Fallback: insert after first paragraph
    first_p_end = content.find('</p>', content.find('PolySniffer'))
    if first_p_end >= 0:
        insert_at = first_p_end + 4
    else:
        insert_at = len(content) // 2
    print(f"\nFallback insertion at {insert_at}")

new_content = content[:insert_at] + images_html + content[insert_at:]

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("Done — both PolySniffer images added.")
else:
    print(f"Error: {r2.text[:300]}")
