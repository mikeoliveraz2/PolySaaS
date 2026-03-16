"""Wrap Request Path image in a white card with padding to prevent edge clipping."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']

# Current block (applied from last fix)
old = '''<div style="text-align:center;margin:15px auto 25px;max-width:700px;">
<img src="https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/dynamic-orchestration-request-path.png" alt="Request Path graph showing event-driven relationships" style="width:100%;max-width:700px;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="color:var(--ps-text-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">Request Path graph: event-driven relationships across entities, categories, and locations</p>
</div>'''

# Card-style: white background with padding so nothing clips at edges.
# The image (1024x600) has: left whitespace, content to right edge, scrollbar at bottom.
# Padding gives the graph content room. overflow:hidden clips the bottom scrollbar artifact.
# The white card approach matches how the image naturally looks (white bg diagram).
new = '''<div style="text-align:center;margin:15px auto 25px;max-width:750px;">
<div style="background:#ffffff;border-radius:10px;padding:12px 16px 4px 8px;box-shadow:0 3px 15px rgba(0,0,0,0.15);overflow:hidden;">
<img src="https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/dynamic-orchestration-request-path.png" alt="Request Path graph showing event-driven relationships" style="width:100%;height:auto;display:block;">
</div>
<p style="color:var(--ps-text-muted,#6B7280);font-size:0.85rem;margin-top:10px;font-style:italic;">Request Path graph: event-driven relationships across entities, categories, and locations</p>
</div>'''

if old in content:
    new_content = content.replace(old, new)
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
    print(f"Update: {r2.status_code}")
    if r2.status_code == 200:
        print("Done — white card wrapper with padding. Content won't clip at edges.")
    else:
        print(f"Error: {r2.text[:300]}")
else:
    print("Old block not found. Searching for current state...")
    idx = content.find('dynamic-orchestration-request-path')
    if idx > 0:
        start = max(0, idx - 400)
        end = min(len(content), idx + 400)
        print(content[start:end])
