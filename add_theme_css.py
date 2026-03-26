"""Add centering CSS via WordPress Additional CSS (custom_css post type).
This CSS is injected at the theme level, not the page content level,
so it has proper priority over theme layout classes.
"""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Check if there's existing custom CSS
r = s.get(f"{AZURE}/wp-json/wp/v2/posts",
          params={"type": "custom_css", "per_page": 10},
          timeout=30)
print(f"Custom CSS posts query: {r.status_code}")

# Try the custom_css endpoint directly
# WordPress stores Additional CSS as a custom post type
# associated with the active theme
r2 = s.get(f"{AZURE}/wp-json/wp/v2/themes", timeout=30)
if r2.status_code == 200:
    themes = r2.json()
    for t in themes:
        stylesheet = t.get('stylesheet', '')
        status = t.get('status', '')
        print(f"  Theme: {stylesheet} ({status})")

# Get current active theme stylesheet
r3 = s.get(f"{AZURE}/wp-json/", timeout=30)
print(f"\nWP API root: {r3.status_code}")

# Try to find/create custom CSS
# WordPress Additional CSS is stored in wp_posts with post_type='custom_css'
# We need to use the /wp/v2/settings or a direct approach
# Let's try fetching via the customizer changeset approach

# Actually, let's just try to add CSS through a different method:
# Create a small plugin-style approach by adding a wp_head style via
# the theme's custom code option, OR by modifying the global styles

# Check if there's a way to add custom CSS
endpoints = [
    '/wp-json/wp/v2/types',
]
for ep in endpoints:
    r4 = s.get(f"{AZURE}{ep}", timeout=15)
    if r4.status_code == 200:
        types = r4.json()
        for name, info in types.items():
            if 'css' in name.lower() or 'style' in name.lower():
                print(f"  Post type: {name} -> {info.get('rest_base', 'no rest_base')}")

# Let's try the direct custom_css approach
# The stylesheet name for Flavor theme
r5 = s.get(f"{AZURE}/wp-json/wp/v2/themes", timeout=15)
if r5.status_code == 200:
    themes = r5.json()
    active = [t for t in themes if t.get('status') == 'active']
    if active:
        stylesheet = active[0].get('stylesheet', '')
        print(f"\nActive theme stylesheet: {stylesheet}")
        
        # Try to get existing custom CSS for this theme
        r6 = s.get(f"{AZURE}/wp-json/wp/v2/posts",
                    params={"status": "publish", "per_page": 100, "_fields": "id,type,title,content"},
                    timeout=30)
        print(f"Posts query: {r6.status_code}")
