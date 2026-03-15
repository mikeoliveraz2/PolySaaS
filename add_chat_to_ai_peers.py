"""
Add the Business Plan Group Chat screenshot to the AI As Peers page,
after the AI Peers Integration or similar section.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")
CHAT_IMG = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/Business-Plan-PolySaaS-Mattermost-03-06-2026_02_23_PM-scaled.png"

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "ai-as-peers", "context": "edit", "_fields": "id,content"
}).json()
aip = pages[0]
raw = aip['content']['raw']

# Find a good insertion point - look for key sections
for kw in ['AI Peers', 'Key Capabilities', 'Integration', 'How It Works', 'capabilities', 'CTA']:
    idx = raw.find(kw)
    if idx >= 0:
        print(f"Found '{kw}' at {idx}")

# Show the last capability card to find the right insertion point
# Look for all the capability cards
cards = list(re.finditer(r'<div style="background:var\(--ps-card-bg', raw))
print(f"\nFound {len(cards)} card divs")
for c in cards:
    text = raw[c.start():c.start()+200]
    heading = re.search(r'<h3[^>]*>([^<]+)</h3>', text)
    if heading:
        print(f"  Card at {c.start()}: {heading.group(1)}")

# Find the last capability card before the CTA/integration section
# We want to insert after the last Key Capabilities card
last_cap_end = None
cap_idx = raw.find('Key Capabilities')
if cap_idx > 0:
    # Find all cards after Key Capabilities
    after_caps = raw[cap_idx:]
    card_matches = list(re.finditer(r'<div style="background:var\(--ps-card-bg', after_caps))
    if card_matches:
        # Find end of last card
        last_card_start = cap_idx + card_matches[-1].start()
        # But we want to insert before CTA, not after the very last card
        # Look for the integration section or CTA
        integration_idx = raw.find('Integration', cap_idx)
        cta_idx = raw.find('Back to Home', cap_idx)
        if cta_idx < 0:
            cta_idx = raw.find('Learn More', cap_idx + 500)
        
        # Find a good spot - after the main capabilities section
        # Insert before the "PolySaaS Integration" or CTA section
        # Find the card that mentions integration
        for c in card_matches:
            abs_pos = cap_idx + c.start()
            text = raw[abs_pos:abs_pos+300]
            if 'Integration' in text or 'integration' in text:
                # Insert before this card
                last_cap_end = abs_pos
                print(f"\nWill insert before Integration card at {last_cap_end}")
                break
        
        if not last_cap_end:
            # Insert after the last capability card
            last_card_abs = cap_idx + card_matches[-1].start()
            depth = 0
            i = last_card_abs
            while i < len(raw):
                if raw[i:i+4] == '<div':
                    depth += 1
                    i += 4
                elif raw[i:i+6] == '</div>':
                    depth -= 1
                    if depth == 0:
                        last_cap_end = i + 6
                        break
                    i += 6
                else:
                    i += 1
            print(f"\nWill insert after last card at {last_cap_end}")

CHAT_BLOCK = f'''
<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:24px;margin-bottom:16px;margin-top:24px;">
<h3 style="color:var(--ps-primary,#001F3F);margin:0 0 12px 0;font-size:1.2rem;">Business Plan Group Chat &mdash; AI As Peers in Action</h3>
<p style="color:var(--ps-text,#1F2937);margin:0 0 16px 0;line-height:1.6;">A simulated Business Plan collaboration session in Mattermost, showcasing how AI agents (Claude CC and Shela) participate alongside team members (Mike) as equal peers. The AI agents contribute strategic analysis, financial projections, and market research in real-time &mdash; demonstrating how PolySaaS transforms team chat into an intelligent, multi-agent workspace where humans and AI work side by side.</p>
<div style="text-align:center;">
<img src="{CHAT_IMG}" alt="PolySaaS Business Plan Group Chat in Mattermost" style="width:100%;max-width:900px;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,0.1);">
</div>
</div>'''

if last_cap_end:
    new_raw = raw[:last_cap_end] + CHAT_BLOCK + raw[last_cap_end:]
    r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{aip['id']}", json={"content": new_raw})
    print(f"\nUpdate: {r.status_code}")
    if r.status_code == 200:
        print("Business Plan Group Chat added to AI As Peers page")
else:
    print("Could not find insertion point!")
