"""Set theme-level Custom CSS through the WordPress custom_css post type."""
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://azure-nightingale-589250.hostingersite.com"
AUTH = ("mikeoliveraz@gmail.com", "XF8j E5IE VpHD N3rx WSkO TaMc")

# First, find the custom_css post for the active theme
# Try both 'kadence' and 'developer' as theme slugs
for theme in ['developer', 'developer-developer', 'developer developer', 'developer//developer', 'kadence']:
    r = requests.get(
        f"{BASE}/wp-json/wp/v2/custom_css",
        auth=AUTH,
        params={"per_page": 100},
        timeout=15
    )
    print(f"Custom CSS endpoint status: {r.status_code}")
    if r.status_code == 200:
        posts = r.json()
        print(f"Found {len(posts)} custom_css posts")
        for p in posts:
            print(f"  ID: {p['id']}, title: {p.get('title', {}).get('rendered', 'N/A')}, status: {p.get('status')}")
            # Show current content
            content = p.get('content', {}).get('rendered', '')
            print(f"  Current CSS: {content[:200]}")
        break
    elif r.status_code == 404:
        print("custom_css endpoint not found, trying next approach...")
    else:
        print(f"Response: {r.text[:200]}")
        break

# Try a different approach - WordPress stores custom CSS as a post type
# Let's search for it
print("\n--- Searching for custom CSS in all post types ---")
for post_type in ['custom_css', 'customize_changeset']:
    r = requests.get(
        f"{BASE}/wp-json/wp/v2/{post_type}",
        auth=AUTH,
        params={"per_page": 5, "status": "any"},
        timeout=15
    )
    print(f"\n{post_type}: status={r.status_code}")
    if r.status_code == 200:
        items = r.json()
        for item in items:
            print(f"  ID={item['id']}, status={item.get('status')}, title={item.get('title',{}).get('rendered','')}")

# Check available REST routes
print("\n--- Checking REST routes for 'css' ---")
r = requests.get(f"{BASE}/wp-json/wp/v2/", auth=AUTH, timeout=15)
if r.status_code == 200:
    data = r.json()
    routes = data.get('routes', {})
    for route in routes:
        if 'css' in route.lower() or 'style' in route.lower():
            print(f"  Route: {route}")
