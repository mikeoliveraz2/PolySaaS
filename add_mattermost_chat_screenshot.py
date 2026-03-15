"""
Add the Business Plan Group Chat screenshot after the AI Peers Integration block
on the Mattermost detail page.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")
CHAT_IMG = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/Business-Plan-PolySaaS-Mattermost-03-06-2026_02_23_PM-scaled.png"

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "mattermost", "context": "edit", "_fields": "id,content"
}).json()
mm = pages[0]
raw = mm['content']['raw']

# Find the AI Peers Integration card block
ai_idx = raw.find('AI Peers Integration</h3>')
if ai_idx < 0:
    print("AI Peers Integration not found!")
    sys.exit(1)

# The AI Peers card is a div with background/border/radius/padding
# Find the closing </div> of this card
card_start = raw.rfind('<div style="background:var(--ps-card-bg', max(0, ai_idx - 200), ai_idx)
if card_start < 0:
    print("Could not find AI Peers card start")
    sys.exit(1)

# Find end of card
depth = 0
i = card_start
card_end = None
while i < len(raw):
    if raw[i:i+4] == '<div':
        depth += 1
        i += 4
    elif raw[i:i+6] == '</div>':
        depth -= 1
        if depth == 0:
            card_end = i + 6
            break
        i += 6
    else:
        i += 1

print(f"AI Peers card: {card_start} to {card_end}")

# Insert the screenshot + description after the AI Peers card
CHAT_BLOCK = f'''
<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:24px;margin-bottom:16px;margin-top:24px;">
<h3 style="color:var(--ps-primary,#001F3F);margin:0 0 12px 0;font-size:1.2rem;">Business Plan Group Chat &mdash; AI As Peers in Action</h3>
<p style="color:var(--ps-text,#1F2937);margin:0 0 16px 0;line-height:1.6;">A simulated Business Plan collaboration session in Mattermost, showcasing how AI agents (Claude CC and Shela) participate alongside team members (Mike) as equal peers. The AI agents contribute strategic analysis, financial projections, and market research in real-time &mdash; demonstrating how PolySaaS transforms team chat into an intelligent, multi-agent workspace where humans and AI work side by side.</p>
<div style="text-align:center;">
<img src="{CHAT_IMG}" alt="PolySaaS Business Plan Group Chat in Mattermost" style="width:100%;max-width:900px;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,0.1);">
</div>
</div>'''

new_raw = raw[:card_end] + CHAT_BLOCK + raw[card_end:]

r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{mm['id']}", json={"content": new_raw})
print(f"Update: {r.status_code}")
if r.status_code == 200:
    print("Business Plan Group Chat screenshot + description added after AI Peers Integration")
