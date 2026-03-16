"""Start fresh — get full page content, find working image style, apply to Request Path."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']

# Find the agent-flow image block (the one that works correctly)
agent_idx = content.find('dynamic-orchestration-agent-flow')
if agent_idx > 0:
    # Get 500 chars around it
    start = max(0, agent_idx - 300)
    end = min(len(content), agent_idx + 300)
    print("=== WORKING image (agent-flow) context ===")
    print(content[start:end])
    print()

# Find the request-path image block (the broken one)
rp_idx = content.find('dynamic-orchestration-request-path')
if rp_idx > 0:
    start = max(0, rp_idx - 300)
    end = min(len(content), rp_idx + 300)
    print("=== BROKEN image (request-path) context ===")
    print(content[start:end])
    print()

# Now fix: Replace the entire request-path image div+img with styling
# that matches the working agent-flow image exactly.

# Find the request-path container div and its closing
# The broken block structure:
old_img_div_start = content.rfind('<div', 0, rp_idx)
# Find the closing </div> after the <p> caption
caption_end = content.find('</div>', rp_idx)

old_section = content[old_img_div_start:caption_end + len('</div>')]
print("=== Section to replace ===")
print(old_section)
print()

# Build the replacement matching the working image style
new_section = '''<div style="text-align:center;margin:15px auto 25px;max-width:700px;">
<img src="https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/dynamic-orchestration-request-path.png" alt="Request Path graph showing event-driven relationships" style="width:100%;max-width:700px;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="color:var(--ps-text-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">Request Path graph: event-driven relationships across entities, categories, and locations</p>
</div>'''

new_content = content.replace(old_section, new_section)

if new_content == content:
    print("ERROR: No replacement made!")
else:
    print(f"Replacement made. Posting...")
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
    print(f"Update: {r2.status_code}")
    if r2.status_code == 200:
        print("Done — Request Path image now uses same style as agent-flow image.")
    else:
        print(f"Error: {r2.text[:300]}")
