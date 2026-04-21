"""Fix Request Path diagram - wider container to prevent clipping."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']

old = 'style="text-align:center;margin:15px auto 25px;max-width:900px;padding:0 20px;"'
new = 'style="text-align:center;margin:15px auto 25px;max-width:100%;padding:0 20px;"'

if old not in content:
    print("Could not find container style!")
    exit(1)

content = content.replace(old, new)

# Also fix the img max-width
old_img = 'max-width:850px;'
new_img = 'max-width:950px;'
content = content.replace(old_img, new_img)

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": content})
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("Done — container widened, image should no longer clip.")
else:
    print(f"Error: {r2.text[:300]}")
