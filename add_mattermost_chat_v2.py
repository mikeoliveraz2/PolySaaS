"""
Add Business Plan Group Chat screenshot after AI Peers Integration on Mattermost page.
V2: broader search for card boundary.
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

ai_idx = raw.find('AI Peers Integration</h3>')
print(f"AI Peers Integration at: {ai_idx}")

# Show 200 chars before to find the card div
before = raw[max(0,ai_idx-300):ai_idx]
print(f"Before:\n{before}\n")

# Find the card start - look for <div with background styling
card_starts = [m.start() + (ai_idx - 300) for m in re.finditer(r'<div style="background:', before)]
if not card_starts:
    card_starts = [m.start() + max(0, ai_idx-300) for m in re.finditer(r'<div style=', before)]

print(f"Potential card starts (absolute): {card_starts}")

if card_starts:
    card_start = card_starts[-1]  # Take the closest one
    print(f"Using card start: {card_start}")
    print(f"Card start text: {raw[card_start:card_start+100]}")
    
    # Find end of this card's closing </div>
    # The card contains the h3 + p, find closing </div> after the p
    # Look for </div> after the AI Peers text
    after_text = raw[ai_idx:]
    # Find the </p> that closes the description
    p_end = after_text.find('</p>')
    if p_end >= 0:
        # The </div> right after </p> closes the card
        div_end = after_text.find('</div>', p_end)
        if div_end >= 0:
            card_end = ai_idx + div_end + 6
            print(f"Card end: {card_end}")
            print(f"Card: {raw[card_start:card_end][:200]}...")
            
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
            print(f"\nUpdate: {r.status_code}")
            if r.status_code == 200:
                print("Done! Business Plan Group Chat added after AI Peers Integration")
