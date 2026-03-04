"""Apply CSS fixes via WordPress Customizer Additional CSS."""
import requests
import json

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

session = requests.Session()
session.auth = (USER, APP_PASS)

# The CSS overrides to fix all identified issues
CSS_FIXES = """
/* ============================================
   PolySaaS Home Page Fixes — Applied by Cursor
   Date: 2026-03-04
   ============================================ */

/* FIX 1: Remove green stripe on Value Proposition container */
#brxe-9d3229 {
    background-image: none !important;
    background-color: transparent !important;
}

/* FIX 2: Fix "Sign Up for a demo" button — lime green to brand blue */
#brxe-spdnfe {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-spdnfe:hover {
    background-color: #03a9f4 !important;
}

/* FIX 3: Fix "Get Early Access" button — mint green to brand blue */
#brxe-108a27 {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-108a27:hover {
    background-color: #03a9f4 !important;
}

/* FIX 4: Fix Value Proposition split background — change to top-down gradient */
#brxe-5a8e5d {
    background-image: linear-gradient(180deg, #e0e0e0, #81d4fa) !important;
}

/* FIX 5: Fix Articles section split background — change to top-down gradient */
#brxe-a41c97 {
    background-image: linear-gradient(180deg, #81d4fa, #e0e0e0) !important;
}

/* FIX 6: Subscription Plans — yellow-grey to blue-grey gradient */
#brxe-d09dd8 {
    background-image: linear-gradient(180deg, #e0e0e0, #81d4fa) !important;
}
"""

# Try method 1: Custom CSS via the customizer settings API
print("Attempting to apply CSS fixes...")

# Check current custom CSS
resp = session.get(f"{SITE}/wp-json/wp/v2/settings")
if resp.status_code == 200:
    print(f"Settings accessible. Status: {resp.status_code}")
else:
    print(f"Settings not accessible: {resp.status_code}")

# Try to find and update the custom CSS option
# WordPress stores Additional CSS in the `custom_css` custom post type
resp = session.get(f"{SITE}/wp-json/wp/v2/types")
if resp.status_code == 200:
    types = resp.json()
    print(f"Available post types: {list(types.keys())}")

# Try the custom_css post type directly
resp = session.get(f"{SITE}/wp-json/wp/v2/custom_css", params={"status": "any", "per_page": 10})
print(f"Custom CSS endpoint: HTTP {resp.status_code}")

if resp.status_code == 404:
    # Custom CSS is stored differently — try via theme mods
    # Get active theme
    resp = session.get(f"{SITE}/wp-json/wp/v2/themes")
    if resp.status_code == 200:
        themes = resp.json()
        for t in themes:
            if t.get('status') == 'active':
                print(f"Active theme: {t['stylesheet']}")
    
    # Try creating a custom CSS post
    # WordPress stores Additional CSS as a post of type 'custom_css'
    # with post_name = theme stylesheet
    print("\nTrying to create/update custom CSS post...")
    
    # First check if one exists
    resp = session.get(f"{SITE}/wp-json/wp/v2/posts", 
                       params={"status": "any", "per_page": 50, "type": "custom_css"})
    print(f"Posts query: HTTP {resp.status_code}")

# Alternative: Try using a page or post to inject CSS
# Actually, let's try the global styles endpoint (WordPress 5.9+)
resp = session.get(f"{SITE}/wp-json/wp/v2/global-styles")
print(f"Global styles: HTTP {resp.status_code}")
if resp.status_code == 200:
    styles = resp.json()
    print(f"  Response: {str(styles)[:300]}")

# Try getting themes for the stylesheet name
resp = session.get(f"{SITE}/wp-json/wp/v2/themes")
print(f"\nThemes endpoint: HTTP {resp.status_code}")
if resp.status_code == 200:
    themes = resp.json()
    for t in themes:
        status = t.get('status', 'unknown')
        name = t.get('name', {})
        if isinstance(name, dict):
            name = name.get('raw', name.get('rendered', 'unknown'))
        stylesheet = t.get('stylesheet', 'unknown')
        print(f"  [{status}] {name} (stylesheet: {stylesheet})")

# The most reliable approach: use wp_options via the settings API
# or just create a simple post with the CSS that we can reference

print("\n" + "="*60)
print("CSS FIXES TO APPLY:")
print("="*60)
print(CSS_FIXES)
print("\nThese fixes need to be applied via:")
print("1. WordPress Customizer > Additional CSS, or")
print("2. Bricks > Settings > Custom CSS, or")
print("3. A Code Snippets plugin")
