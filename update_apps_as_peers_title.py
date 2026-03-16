"""Update Apps As Peers page title to include (Available Q2 2026)."""
import requests, re

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=apps-as-peers&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']

# Find the title H2
old_title = '>Apps As Peers</h2>'
new_title = '>Apps As Peers (Available Q2 2026)</h2>'

if old_title in content:
    content = content.replace(old_title, new_title)
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": content})
    print(f"Update: {r2.status_code}")
    if r2.status_code == 200:
        print("Done — title updated to 'Apps As Peers (Available Q2 2026)'")
    else:
        print(f"Error: {r2.text[:300]}")
else:
    print("Title not found or already updated")
    # Check what's there
    match = re.search(r'>Apps As Peers[^<]*</h2>', content)
    if match:
        print(f"Current: {match.group()}")
