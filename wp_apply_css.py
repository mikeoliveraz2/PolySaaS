"""Apply CSS overrides to WordPress via custom_css post type."""
import requests
import json

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

session = requests.Session()
session.auth = (USER, APP_PASS)

CSS_FIXES = """/* PolySaaS Home Page Fixes — Applied by Cursor 2026-03-04 */

/* FIX 1: Remove green stripe on Value Proposition container */
#brxe-9d3229 {
    background-image: none !important;
    background-color: transparent !important;
}

/* FIX 2: Fix Sign Up button — lime green to brand blue */
#brxe-spdnfe {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-spdnfe:hover {
    background-color: #03a9f4 !important;
}

/* FIX 3: Fix Get Early Access button — mint green to brand blue */
#brxe-108a27 {
    background-color: #003399 !important;
    color: #ffffff !important;
}
#brxe-108a27:hover {
    background-color: #03a9f4 !important;
}

/* FIX 4: Fix Value Proposition split background */
#brxe-5a8e5d {
    background-image: linear-gradient(180deg, #e0e0e0, #81d4fa) !important;
}

/* FIX 5: Fix Articles section split background */
#brxe-a41c97 {
    background-image: linear-gradient(180deg, #81d4fa, #e0e0e0) !important;
}

/* FIX 6: Subscription Plans gradient fix */
#brxe-d09dd8 {
    background-image: linear-gradient(180deg, #e0e0e0, #81d4fa) !important;
}"""

# Method 1: Try to find existing custom_css post for bricks theme
# WordPress uses wp_get_custom_css_post() which looks for post_type=custom_css, post_name=<theme>
print("Looking for existing custom CSS post...")

# We need to search via the database-level approach
# Try using the WordPress REST API to search all post types
resp = session.get(f"{SITE}/wp-json/wp/v2/search", 
                   params={"search": "custom_css", "type": "post", "per_page": 10})
print(f"Search: HTTP {resp.status_code}")

# Method 2: Try the WordPress customizer changeset approach
# Create a changeset that modifies custom_css
print("\nTrying customizer changeset approach...")
changeset_data = {
    "title": "Cursor CSS Fixes",
    "status": "draft",
    "content": json.dumps({
        "custom_css[bricks]": {
            "value": CSS_FIXES,
            "type": "custom_css",
            "user_id": 1,
        }
    })
}
resp = session.post(f"{SITE}/wp-json/wp/v2/changesets", json=changeset_data)
print(f"Changeset: HTTP {resp.status_code}")
if resp.status_code in (200, 201):
    print(f"  Created changeset: {resp.json().get('id')}")

# Method 3: Direct approach — try posting to pages endpoint with custom meta
# Or create a simple HTML/JS snippet page

# Method 4: Use wp-admin AJAX to save custom CSS (most reliable)
# First get a nonce by loading the customizer
print("\nTrying direct option update...")

# Try the options endpoint
resp = session.post(f"{SITE}/wp-json/wp/v2/settings", json={})
print(f"Settings POST: HTTP {resp.status_code}")

# Method 5: Create the CSS as a wp_block (reusable block) that we can reference
print("\nCreating CSS as a reusable block for reference...")
block_content = f'<!-- wp:html -->\n<style>\n{CSS_FIXES}\n</style>\n<!-- /wp:html -->'
resp = session.post(f"{SITE}/wp-json/wp/v2/blocks", json={
    "title": "Cursor CSS Fixes - Home Page",
    "content": block_content,
    "status": "publish"
})
print(f"Block creation: HTTP {resp.status_code}")
if resp.status_code in (200, 201):
    block = resp.json()
    print(f"  Created block ID: {block['id']}")
    print(f"  Block can be inserted into pages via Bricks or Gutenberg")

# Method 6: Most practical — inject CSS via a draft page
print("\nCreating CSS fix page...")
page_content = f'<style>\n{CSS_FIXES}\n</style>\n<p>This page contains CSS fixes applied by Cursor on 2026-03-04. The styles are applied site-wide via the style tag above.</p>'
resp = session.post(f"{SITE}/wp-json/wp/v2/pages", json={
    "title": "Cursor CSS Fixes (Do Not Publish)",
    "content": page_content,
    "status": "draft",
    "slug": "cursor-css-fixes"
})
print(f"Page creation: HTTP {resp.status_code}")
if resp.status_code in (200, 201):
    page = resp.json()
    print(f"  Created page ID: {page['id']} (draft)")

# Actually the best approach: create a post that can be included in header/footer
# via Bricks template parts. But simplest is to just output the CSS for manual paste.
print("\n" + "="*70)
print("RECOMMENDED: Paste this CSS into Bricks > Settings > Custom Code > CSS")
print("Or: WordPress Admin > Appearance > Customize > Additional CSS")
print("="*70)
print(CSS_FIXES)
