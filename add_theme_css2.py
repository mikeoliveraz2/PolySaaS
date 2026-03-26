"""Add centering CSS via WordPress global styles or custom CSS approach."""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# 1) Try global styles
r = s.get(f"{AZURE}/wp-json/wp/v2/global-styles", timeout=15)
print(f"Global styles list: {r.status_code}")
if r.status_code == 200:
    items = r.json()
    for item in items:
        print(f"  ID: {item.get('id')}, Title: {item.get('title')}")

# 2) Try getting the page with full content and check how features are structured
# Let's get the homepage and look at the exact wp-block-columns structure
r2 = s.get(f"{AZURE}/wp-json/wp/v2/pages",
           params={"slug": "home", "context": "edit", "_fields": "id"},
           timeout=30)
page_id = r2.json()[0]['id']
print(f"\nHome page ID: {page_id}")

# 3) Let's try a completely different approach - use the page's own layout meta
# Kadence uses _kad_post_layout meta to control the content width
r3 = s.get(f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
           params={"context": "edit", "_fields": "id,meta"},
           timeout=30)
meta = r3.json().get('meta', {})
print("\nAll meta keys:")
for k, v in meta.items():
    print(f"  {k} = {v}")

# 4) Try setting Kadence page-specific meta for fullwidth/narrow layout
# Common Kadence meta keys:
# _kad_post_layout - page layout
# _kad_post_content_style - content style
# _kad_post_vertical_padding - vertical padding
# _kad_post_sidebar_id - sidebar
# _kad_post_feature - feature image
# _kad_post_title - title display
# _kad_post_content_width - content width
print("\n=== Attempting to set layout meta ===")
