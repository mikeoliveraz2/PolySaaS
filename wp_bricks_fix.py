"""Read and fix Bricks element styles via WordPress REST API."""
import requests
import json

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

session = requests.Session()
session.auth = (USER, APP_PASS)

# Step 1: Find the Home page ID
print("Finding Home page...")
pages = session.get(f"{SITE}/wp-json/wp/v2/pages", params={"slug": "home", "status": "any"}).json()
if not pages:
    # Try getting the front page
    pages = session.get(f"{SITE}/wp-json/wp/v2/pages", params={"per_page": 50, "status": "any"}).json()
    for p in pages:
        print(f"  ID:{p['id']:5d}  slug:{p['slug']:30s}  title:{p['title']['rendered']}")

# Step 2: Try to read meta for the home page
print("\nChecking if Bricks meta is accessible...")
for page in pages:
    page_id = page['id']
    title = page['title']['rendered']
    
    # Try getting the page with meta context
    resp = session.get(f"{SITE}/wp-json/wp/v2/pages/{page_id}", params={"context": "edit"})
    if resp.status_code == 200:
        data = resp.json()
        meta = data.get('meta', {})
        if meta:
            print(f"\n  Page '{title}' (ID:{page_id}) has meta keys: {list(meta.keys())}")
            # Check for Bricks-specific meta
            for key in meta:
                if 'bricks' in key.lower():
                    val = meta[key]
                    if isinstance(val, str) and len(val) > 0:
                        print(f"    {key}: {val[:200]}...")
                    elif isinstance(val, list) and len(val) > 0:
                        print(f"    {key}: list with {len(val)} items")
                        if len(val) > 0:
                            print(f"      First item keys: {list(val[0].keys()) if isinstance(val[0], dict) else type(val[0])}")
                    elif isinstance(val, dict):
                        print(f"    {key}: dict with keys {list(val.keys())}")
                    else:
                        print(f"    {key}: {type(val).__name__} = {val}")
        else:
            if title in ('Home', ''):
                print(f"\n  Page '{title}' (ID:{page_id}) - no meta exposed via REST API")
    else:
        print(f"  Page '{title}' (ID:{page_id}) - HTTP {resp.status_code}")
    
    # Only check Home and the frontpage
    if title in ('Home', '') or page['slug'] == 'home':
        # Also try custom endpoint that Bricks might expose
        for endpoint in [
            f"{SITE}/wp-json/bricks/v1/get_page_data/{page_id}",
            f"{SITE}/wp-json/bricks/v1/render_element",
        ]:
            resp2 = session.get(endpoint)
            print(f"  Bricks API {endpoint.split('/')[-2:]}: HTTP {resp2.status_code}")
            if resp2.status_code == 200:
                print(f"    Response: {str(resp2.json())[:300]}")
