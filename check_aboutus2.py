"""Get full About Us page raw content"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content,title"
})
pages = {p['slug']: p for p in r.json()}

about = pages['about-us']
raw = about['content']['raw']
print(f"Total raw content length: {len(raw)}")
print("=" * 80)
print(raw)
