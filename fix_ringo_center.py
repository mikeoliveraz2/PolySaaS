"""Center Ringo Rivera's headshot on About Us page."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=about-us&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']

old = '<img src="https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/ringo-rivera-headshot.jpg" alt="Ringo Rivera" style="width:120px;height:120px;border-radius:50%;object-fit:cover;margin-bottom:12px;">'
new = '<img src="https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/ringo-rivera-headshot.jpg" alt="Ringo Rivera" style="display:block;margin:0 auto 12px auto;width:120px;height:120px;border-radius:50%;object-fit:cover;">'

if old not in content:
    print("Could not find Ringo image tag!")
    exit(1)

new_content = content.replace(old, new)
r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("Done — Ringo headshot centered.")
else:
    print(f"Error: {r2.text[:300]}")
