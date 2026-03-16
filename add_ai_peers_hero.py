"""Add android conference table image as hero shot on AI As Peers page."""
import requests, re

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Use the conference table image (id=980, the newer one)
HERO_IMG = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2025/12/AIAsPeers-conference-Table-1.webp"

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=ai-as-peers&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']
print(f"AI As Peers page id={pid}, length={len(content)}")

# Check existing images
imgs = re.findall(r'<img[^>]+alt="([^"]*)"', content)
print(f"Current images: {imgs}")

# Find the title H2
title_idx = content.find('>AI As Peers</h2>')
if title_idx < 0:
    print("Title not found!")
    exit(1)

# Find the end of the title block (<!-- /wp:html --> after title)
title_end = title_idx + len('>AI As Peers</h2>')
wp_close = content.find('<!-- /wp:html -->', title_end, title_end + 50)
if wp_close >= 0:
    insert_at = wp_close + len('<!-- /wp:html -->')
else:
    insert_at = title_end

print(f"Inserting hero image after title at position {insert_at}")

hero_html = '''
<!-- wp:html -->
<div style="text-align:center;margin:15px auto 10px;">
<img src="{img}" alt="AI As Peers — androids collaborating as team members" style="width:100%;max-width:800px;border-radius:12px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
</div>
<!-- /wp:html -->
'''.format(img=HERO_IMG)

new_content = content[:insert_at] + hero_html + content[insert_at:]

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("Done — hero image added to AI As Peers page.")
else:
    print(f"Error: {r2.text[:300]}")
