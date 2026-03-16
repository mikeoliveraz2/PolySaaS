"""Center the hero image on AI As Peers page."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=ai-as-peers&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']

old = 'alt="AI As Peers — androids collaborating as team members" style="width:100%;max-width:800px;border-radius:12px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">'
new = 'alt="AI As Peers — androids collaborating as team members" style="display:block;margin:0 auto;width:100%;max-width:800px;border-radius:12px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">'

if old not in content:
    print("Could not find image tag!")
    exit(1)

new_content = content.replace(old, new)
r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("Done — hero image centered.")
else:
    print(f"Error: {r2.text[:300]}")
