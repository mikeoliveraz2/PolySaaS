"""Fix the third video title on Gallery Videos page."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages",
          params={"slug": "gallery-videos", "context": "edit", "_fields": "id,content"},
          timeout=30)
page = r.json()[0]
raw = page['content']['raw']

old = "PolySaaS demo of PolySniffer data mapping tool"
new = "About PolySaaS"
raw = raw.replace(old, new)
print(f"  '{old}' -> '{new}'")

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page['id']}",
            json={"content": raw}, timeout=30)
print(f"  Status: {r2.status_code}")
