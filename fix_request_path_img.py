"""Fix Request Path diagram - center and prevent clipping."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=dynamic-orchestration&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']

old = '<div style="text-align:center;margin:15px auto 25px;max-width:700px;">\n<img src="https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/dynamic-orchestration-request-path.png" alt="Request Path graph showing event-driven relationships" style="width:100%;border-radius:10px;box-shadow:0 3px 12px rgba(0,0,0,0.1);">'

new = '<div style="text-align:center;margin:15px auto 25px;max-width:900px;padding:0 20px;">\n<img src="https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/dynamic-orchestration-request-path.png" alt="Request Path graph showing event-driven relationships" style="display:block;margin:0 auto;width:100%;max-width:850px;border-radius:10px;box-shadow:0 3px 12px rgba(0,0,0,0.1);">'

if old not in content:
    print("Could not find image tag! Trying alternate...")
    # Try finding just the img src
    img_idx = content.find('dynamic-orchestration-request-path')
    if img_idx > 0:
        print(f"Found at {img_idx}")
        # Show surrounding context
        start = content.rfind('<div', max(0, img_idx - 200), img_idx)
        end = content.find('<!-- /wp:html -->', img_idx)
        print(content[start:end])
    exit(1)

new_content = content.replace(old, new)
r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("Done — Request Path image centered and unclipped.")
else:
    print(f"Error: {r2.text[:300]}")
