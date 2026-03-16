"""Add trust line under pricing cards on the Pricing page."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=pricing&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']

# Find the existing footer text area
old = '<div style="text-align:center;max-width:700px;margin:0 auto 20px;">'

if old not in content:
    print("Could not find footer text area!")
    print("Searching for alternatives...")
    idx = content.find('All plans include core PolySaaS features')
    if idx > 0:
        div_start = content.rfind('<div', max(0, idx-200), idx)
        print(f"Found 'All plans' at {idx}, div starts at {div_start}")
        snippet = content[div_start:div_start+100]
        print(f"Snippet: {snippet}")
    exit(1)

trust_line = '''<p style="color:var(--ps-text-muted,#6B7280);font-size:0.85rem;margin-top:12px;letter-spacing:0.3px;">Powered by Stripe &middot; Cancel anytime &middot; 14-day free trial on all plans</p>'''

new = f'<div style="text-align:center;max-width:700px;margin:0 auto 20px;">\n{trust_line}'

new_content = content.replace(old, new)

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("Done — trust line added under pricing cards.")
else:
    print(f"Error: {r2.text[:300]}")
