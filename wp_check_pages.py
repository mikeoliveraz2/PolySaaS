"""Check which pages have content vs Bricks-only."""
import requests
from html import unescape

SITE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

for kind in ['pages', 'posts']:
    print(f"\n=== {kind.upper()} ===")
    resp = s.get(f"{SITE}/wp-json/wp/v2/{kind}", params={"per_page": 50, "status": "any"})
    items = resp.json()
    for p in items:
        title = unescape(p['title']['rendered'])
        clen = len(p['content']['rendered'].strip())
        status = p['status']
        print(f"  [{status:8s}] {title:45s} content: {clen:5d} chars")
