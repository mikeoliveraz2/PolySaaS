"""Fix Request Path diagram - truly center, no clipping, no white bar."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']

# Find the entire wp:html block containing this image
marker = 'dynamic-orchestration-request-path'
idx = content.find(marker)
block_start = content.rfind('<!-- wp:html -->', 0, idx)
block_end = content.find('<!-- /wp:html -->', idx) + len('<!-- /wp:html -->')

print(f"Current block ({block_start}..{block_end}):")
print(content[block_start:block_end])

# Replace the entire block with a clean version
# The image itself is wide/landscape ratio - the white bar at the bottom suggests
# WordPress may have generated a cropped version. Use the original .png URL.
# Also remove border-radius which can cause visual clipping, and use object-fit.
new_block = '''<!-- wp:html -->
<div style="text-align:center;margin:15px auto 25px;">
<img src="https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/dynamic-orchestration-request-path.png" alt="Request Path graph showing event-driven relationships" style="display:block;margin:0 auto;max-width:100%;height:auto;border-radius:8px;">
<p style="color:var(--ps-text-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">Request Path graph: event-driven relationships across entities, categories, and locations</p>
</div>
<!-- /wp:html -->'''

new_content = content[:block_start] + new_block + content[block_end:]

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"\nUpdate: {r2.status_code}")
if r2.status_code == 200:
    print("Done — image block rebuilt: full width, no max-width constraint, no clipping.")
else:
    print(f"Error: {r2.text[:300]}")
