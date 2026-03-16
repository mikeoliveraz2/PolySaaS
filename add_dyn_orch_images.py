"""Add the two new Dynamic Orchestration diagrams to the page."""
import requests, re

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

IMG1 = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/dynamic-orchestration-agent-flow.jpg"
IMG2 = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/dynamic-orchestration-event-bus.jpg"

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']
print(f"Dynamic Orchestration page id={pid}, length={len(content)}")

# Check existing images
imgs = re.findall(r'<img[^>]+alt="([^"]*)"', content)
print(f"Current images: {imgs}")

# Find the title and subtitle area to insert after
title_idx = content.find('>Dynamic Orchestration</h2>')
if title_idx < 0:
    # Try with the (Available Q2 2026) suffix or similar
    title_idx = content.find('Dynamic Orchestration')
    print(f"Title found at: {title_idx}")

# Find the subtitle or intro paragraph
subtitle_idx = content.find('Intelligent Workflow')
if subtitle_idx < 0:
    subtitle_idx = content.find('orchestrat', title_idx + 20)
print(f"Subtitle area at: {subtitle_idx}")

# Find Key Capabilities section as the insertion boundary
key_cap_idx = content.find('Key Capabilities')
print(f"Key Capabilities at: {key_cap_idx}")

# Build the image block to insert before Key Capabilities
images_html = '''
<!-- wp:html -->
<div style="display:flex;flex-wrap:wrap;gap:24px;justify-content:center;margin:20px auto 30px;max-width:1000px;">
<div style="flex:1 1 450px;max-width:500px;text-align:center;">
<img src="{img1}" alt="Dynamic Orchestration — Agent Task Execution Flow" style="width:100%;border-radius:10px;box-shadow:0 3px 12px rgba(0,0,0,0.1);">
<p style="color:var(--ps-text-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">Agent-based orchestration: User Interface → Orchestrator → Task Agents → MCP Server</p>
</div>
<div style="flex:1 1 450px;max-width:500px;text-align:center;">
<img src="{img2}" alt="Dynamic Orchestration — Event-Based Architecture" style="width:100%;border-radius:10px;box-shadow:0 3px 12px rgba(0,0,0,0.1);">
<p style="color:var(--ps-text-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">Event-based architecture: Central Event Bus connecting domain orchestration frameworks</p>
</div>
</div>
<!-- /wp:html -->
'''.format(img1=IMG1, img2=IMG2)

if key_cap_idx > 0:
    # Find the wp:html block start before Key Capabilities
    block_start = content.rfind('<!-- wp:html -->', 0, key_cap_idx)
    insert_at = block_start if block_start > 0 else key_cap_idx
    print(f"Inserting images at position {insert_at}")
    new_content = content[:insert_at] + images_html + content[insert_at:]
else:
    # Insert after the intro paragraph
    print("No Key Capabilities found, inserting after intro")
    # Find end of first wp:html block after title
    wp_close = content.find('<!-- /wp:html -->', title_idx)
    if wp_close > 0:
        insert_at = wp_close + len('<!-- /wp:html -->')
        new_content = content[:insert_at] + images_html + content[insert_at:]
    else:
        print("Cannot find insertion point!")
        exit(1)

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("Done — Dynamic Orchestration diagrams added.")
else:
    print(f"Error: {r2.text[:300]}")
