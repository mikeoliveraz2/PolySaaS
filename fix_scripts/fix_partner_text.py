"""Fix partner text color above CTA button on About Us."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/1345",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

old = 'style="font-size:0.9rem;margin-bottom:6px;color:#6B7280">Whether as a partner, investor, or team member'
new = 'style="font-size:0.9rem;margin-bottom:6px;color:#111827">Whether as a partner, investor, or team member'

if old in content:
    content = content.replace(old, new)
    print("Changed partner text color from #6B7280 to #111827")
else:
    print("Text not found!")
    sys.exit(1)

r2 = requests.post(BASE + "/wp-json/wp/v2/pages/1345",
                   auth=AUTH,
                   json={"content": content},
                   timeout=45)
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("SUCCESS")
else:
    print(f"Error: {r2.text[:300]}")
