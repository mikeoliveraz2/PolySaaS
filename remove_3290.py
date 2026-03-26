"""Remove the 3290.jpg image (directly under Mike's headshot) from Gallery Images."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages",
          params={"slug": "gallery-images", "context": "edit", "_fields": "id,content"},
          timeout=30)
page = r.json()[0]
raw = page['content']['raw']
page_id = page['id']
print(f"Page ID: {page_id}, length: {len(raw)} chars")

target = "3290.jpg"
idx = raw.find(target)
if idx < 0:
    print(f"  ERROR: '{target}' not found on page")
    sys.exit(1)

item_start = raw.rfind('<div style="break-inside:avoid', max(0, idx - 300), idx)
item_end_tag = raw.find('</div>', idx)
item_end = raw.find('</div>', item_end_tag + 1) + 6

snippet = raw[item_start:item_end]
print(f"  Found at {item_start}:{item_end} ({len(snippet)} chars)")
print(f"  Snippet: {snippet[:200]}...")

raw = raw[:item_start] + raw[item_end:]
print(f"\n  Removed. New length: {len(raw)} chars")

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
            json={"content": raw}, timeout=30)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    print("  SUCCESS! 3290.jpg image removed from gallery.")
else:
    print(f"  ERROR: {r2.text[:500]}")
