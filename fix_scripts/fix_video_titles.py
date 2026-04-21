"""Fix the video titles on Gallery Videos page to match actual YouTube titles."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

TITLE_FIXES = [
    ("PolySaaS Platform Overview", "PolySaaS Overview 5"),
    ("PolySaaS Demo", "PolySniffer feature of PolySaaS"),
    ("PolySaaS Walkthrough", "PolySaaS demo of PolySniffer data mapping tool"),
]

print("=== Fetching Gallery Videos page ===")
r = s.get(f"{AZURE}/wp-json/wp/v2/pages",
          params={"slug": "gallery-videos", "context": "edit", "_fields": "id,content"},
          timeout=30)
page = r.json()[0]
raw = page['content']['raw']
page_id = page['id']

for old_title, new_title in TITLE_FIXES:
    if old_title in raw:
        raw = raw.replace(old_title, new_title)
        print(f"  '{old_title}' -> '{new_title}'")
    else:
        print(f"  WARNING: '{old_title}' not found")

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
            json={"content": raw}, timeout=30)
print(f"\n  Status: {r2.status_code}")
if r2.status_code == 200:
    print("  SUCCESS! Video titles updated.")
else:
    print(f"  ERROR: {r2.text[:500]}")
