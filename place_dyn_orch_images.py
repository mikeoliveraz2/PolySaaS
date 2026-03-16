"""Place Dynamic Orchestration diagrams after their matching capability blocks.
- Agent flow (dyn_orch2) -> after Atomic Services
- Event bus (dyna_orch3) -> after Dynamic Customization
"""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

IMG_AGENT = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/dynamic-orchestration-agent-flow.jpg"
IMG_EVENT = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/dynamic-orchestration-event-bus.jpg"

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']
print(f"Page length: {len(content)}")

# Step 1: Remove the existing combined image block
marker = 'dynamic-orchestration-agent-flow'
marker_idx = content.find(marker)
if marker_idx > 0:
    block_start = content.rfind('<!-- wp:html -->', 0, marker_idx)
    block_end = content.find('<!-- /wp:html -->', marker_idx) + len('<!-- /wp:html -->')
    print(f"Removing combined image block: {block_start}..{block_end}")
    content = content[:block_start] + content[block_end:]
else:
    print("Combined image block not found, continuing...")

# Step 2: Find the capability sections
atomic_idx = content.find('Atomic Services</h3>')
dynamic_cust_idx = content.find('Dynamic Customization</h3>')
print(f"Atomic Services H3 at: {atomic_idx}")
print(f"Dynamic Customization H3 at: {dynamic_cust_idx}")

# Build individual image blocks
agent_img_block = '''
<!-- wp:html -->
<div style="text-align:center;margin:15px auto 25px;max-width:700px;">
<img src="{img}" alt="Dynamic Orchestration — Agent Task Execution Flow" style="width:100%;border-radius:10px;box-shadow:0 3px 12px rgba(0,0,0,0.1);">
<p style="color:var(--ps-text-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">Agent-based orchestration: User Interface → Orchestrator → Task Agents → MCP Server</p>
</div>
<!-- /wp:html -->'''.format(img=IMG_AGENT)

event_img_block = '''
<!-- wp:html -->
<div style="text-align:center;margin:15px auto 25px;max-width:700px;">
<img src="{img}" alt="Dynamic Orchestration — Event-Based Architecture" style="width:100%;border-radius:10px;box-shadow:0 3px 12px rgba(0,0,0,0.1);">
<p style="color:var(--ps-text-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">Event-based architecture: Central Event Bus connecting domain orchestration frameworks</p>
</div>
<!-- /wp:html -->'''.format(img=IMG_EVENT)

# Step 3: Insert event bus image after Dynamic Customization block (do this first since it's later in the content)
# Find the end of the Dynamic Customization description paragraph
dc_para_end = content.find('</p>', dynamic_cust_idx)
# Find the closing </div> of the capability card
dc_div_end = content.find('</div>', dc_para_end)
if dc_div_end > 0:
    insert_dc = dc_div_end + len('</div>')
    content = content[:insert_dc] + event_img_block + content[insert_dc:]
    print(f"Inserted event bus image after Dynamic Customization at {insert_dc}")
else:
    print("Could not find Dynamic Customization card end!")

# Step 4: Insert agent flow image after Atomic Services block
# Re-find Atomic Services since positions may have shifted
atomic_idx = content.find('Atomic Services</h3>')
as_para_end = content.find('</p>', atomic_idx)
as_div_end = content.find('</div>', as_para_end)
if as_div_end > 0:
    insert_as = as_div_end + len('</div>')
    content = content[:insert_as] + agent_img_block + content[insert_as:]
    print(f"Inserted agent flow image after Atomic Services at {insert_as}")
else:
    print("Could not find Atomic Services card end!")

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": content})
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("Done — each diagram placed after its matching capability block.")
else:
    print(f"Error: {r2.text[:300]}")
