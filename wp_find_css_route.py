"""Find the correct WordPress route for custom CSS and apply it."""
import requests
import json

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

session = requests.Session()
session.auth = (USER, APP_PASS)

# Check all available REST API routes
print("Checking all REST API routes...")
resp = session.get(f"{SITE}/wp-json/")
if resp.status_code == 200:
    api = resp.json()
    routes = api.get('routes', {})
    print(f"Total routes: {len(routes)}")
    for route in sorted(routes.keys()):
        if any(k in route.lower() for k in ['css', 'style', 'custom', 'theme', 'changeset']):
            methods = []
            for ep in routes[route].get('endpoints', []):
                methods.extend(ep.get('methods', []))
            print(f"  {route}  [{', '.join(set(methods))}]")

# Check post types
print("\nChecking post types...")
resp = session.get(f"{SITE}/wp-json/wp/v2/types")
if resp.status_code == 200:
    types = resp.json()
    for name, info in types.items():
        rest_base = info.get('rest_base', '')
        print(f"  {name:30s}  rest_base: {rest_base}")

# Try different endpoint patterns for custom_css
endpoints_to_try = [
    '/wp-json/wp/v2/custom_css',
    '/wp-json/wp/v2/custom-css',
    '/wp-json/wp/v2/custom_css/bricks',
    '/wp-json/wp/v2/custom-css/bricks',
    '/wp-json/wp/v2/global-styles',
    '/wp-json/wp/v2/global-styles?per_page=10',
]

print("\nTrying endpoints for custom CSS...")
for ep in endpoints_to_try:
    resp = session.get(f"{SITE}{ep}")
    print(f"  {ep:50s} → HTTP {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, list):
            for item in data[:3]:
                print(f"    ID: {item.get('id')}, Title: {item.get('title', {})}")
        elif isinstance(data, dict):
            print(f"    Keys: {list(data.keys())[:10]}")

# Try to list all posts including custom_css type
print("\nSearching for custom_css posts via search...")
resp = session.get(f"{SITE}/wp-json/wp/v2/search", params={
    "search": "css",
    "type": "post",
    "per_page": 20,
})
if resp.status_code == 200:
    results = resp.json()
    for r in results:
        print(f"  ID={r.get('id')}: {r.get('title', '')} [{r.get('type', '')}/{r.get('subtype', '')}]")

# Check global styles in detail
print("\nGlobal Styles detail...")
resp = session.get(f"{SITE}/wp-json/wp/v2/global-styles")
if resp.status_code == 200:
    styles = resp.json()
    if isinstance(styles, list):
        for gs in styles:
            gs_id = gs.get('id')
            print(f"  Global Style ID: {gs_id}")
            print(f"  Title: {gs.get('title', {})}")
            css_val = gs.get('styles', {}).get('css', '')
            if css_val:
                print(f"  Has CSS: {len(css_val)} chars")
            
            # Try updating global styles with our CSS
            print(f"\n  Attempting to update global style {gs_id} with custom CSS...")
            current_styles = gs.get('styles', {})
            current_styles['css'] = "/* PolySaaS Site-Wide Brand Uniformity CSS */"
            update_resp = session.post(
                f"{SITE}/wp-json/wp/v2/global-styles/{gs_id}",
                json={"styles": current_styles}
            )
            print(f"  Update response: HTTP {update_resp.status_code}")
            if update_resp.status_code == 200:
                print("  Global styles updated!")
            else:
                print(f"  Error: {update_resp.text[:200]}")
