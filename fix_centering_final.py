"""Fix homepage feature block centering using two approaches:
1. Set Kadence page meta to 'boxed' content style
2. Add CSS via WordPress custom_css post type (Additional CSS in Customizer)
"""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

HOME_PAGE_ID = 1313

# ── Step 1: Set Kadence page meta to 'boxed' content style ──
print("Step 1: Setting Kadence page meta for boxed content...")
r1 = s.post(
    f"{AZURE}/wp-json/wp/v2/pages/{HOME_PAGE_ID}",
    json={
        "meta": {
            "_kad_post_content_style": "boxed",
            "_kad_post_layout": "normal",
        }
    },
    timeout=30
)
print(f"  Page meta update: {r1.status_code}")
if r1.status_code == 200:
    meta = r1.json().get('meta', {})
    print(f"  _kad_post_content_style = {meta.get('_kad_post_content_style')}")
    print(f"  _kad_post_layout = {meta.get('_kad_post_layout')}")
else:
    print(f"  Error: {r1.text[:300]}")

# ── Step 2: Add CSS via custom_css post type ──
print("\nStep 2: Adding Additional CSS via custom_css post type...")

# WordPress stores Additional CSS as a post with post_type='custom_css'
# and post_name = active theme stylesheet name
# First, check if one already exists for 'kadence'
r2 = s.get(
    f"{AZURE}/wp-json/wp/v2/posts",
    params={"per_page": 100, "status": "any", "_fields": "id,type,status,title,slug"},
    timeout=30
)

# The custom_css post type might not be exposed via REST by default.
# Let's try a different approach - use the customize API or
# check for the wp_css_keywords endpoint
print(f"  Posts query: {r2.status_code}")

# Let's try to check if custom_css is a registered REST route
r3 = s.get(f"{AZURE}/wp-json/wp/v2/types", timeout=15)
types = r3.json()
print(f"  Available post types: {list(types.keys())}")

# Check if custom_css is available
if 'custom_css' in types:
    rest_base = types['custom_css'].get('rest_base', 'custom_css')
    print(f"  custom_css rest_base: {rest_base}")
else:
    print("  custom_css type not in REST API")

# Try global-styles approach (WordPress 5.9+ Full Site Editing)
if 'wp_global_styles' in types:
    rest_base = types['wp_global_styles'].get('rest_base', 'global-styles')
    print(f"  wp_global_styles rest_base: {rest_base}")
    r4 = s.get(f"{AZURE}/wp-json/wp/v2/{rest_base}", timeout=15)
    print(f"  global-styles list: {r4.status_code}")
    if r4.status_code == 200 and r4.json():
        for item in r4.json():
            print(f"    ID: {item.get('id')}, Title: {item.get('title')}")

# ── Step 3: Alternative - inject CSS into the page <style> block ──
# Since custom_css may not be REST-accessible, let's add a properly
# scoped <style> block at the very TOP of the page content
print("\nStep 3: Adding high-priority centering CSS to page content...")
r5 = s.get(
    f"{AZURE}/wp-json/wp/v2/pages/{HOME_PAGE_ID}",
    params={"context": "edit", "_fields": "content"},
    timeout=30
)
content = r5.json()['content']['raw']

# The centering CSS - targets the Platform Features section specifically
CENTERING_CSS = """/* PolySaaS Feature Block Centering */
.entry-content .wp-block-columns.is-layout-flex {
  max-width: 1100px !important;
  margin-left: auto !important;
  margin-right: auto !important;
}
.entry-content .wp-block-group .wp-block-group__inner-container {
  max-width: 1100px !important;
  margin-left: auto !important;
  margin-right: auto !important;
}
.entry-content-wrap {
  max-width: 1200px !important;
  margin-left: auto !important;
  margin-right: auto !important;
}"""

# Check if there's already a <style> block at the top
if content.startswith('<style>'):
    # Replace existing style block
    style_end = content.find('</style>') + len('</style>')
    old_style = content[:style_end]
    # Check if centering CSS is already there
    if 'Feature Block Centering' in old_style:
        print("  Centering CSS already present - skipping")
    else:
        # Inject before the closing </style>
        new_style = old_style.replace('</style>', CENTERING_CSS + '\n</style>')
        content = new_style + content[style_end:]
        print("  Added centering CSS to existing style block")
elif '<style>' in content[:5000]:
    # Style block exists but not at very top
    style_start = content.find('<style>')
    style_end = content.find('</style>') + len('</style>')
    old_style = content[style_start:style_end]
    if 'Feature Block Centering' in old_style:
        print("  Centering CSS already present - skipping")
    else:
        new_style = old_style.replace('</style>', CENTERING_CSS + '\n</style>')
        content = content[:style_start] + new_style + content[style_end:]
        print("  Added centering CSS to existing style block")
else:
    # No style block - create one at the top
    content = f'<style>{CENTERING_CSS}\n</style>\n' + content
    print("  Created new style block with centering CSS")

# Now update the page
r6 = s.post(
    f"{AZURE}/wp-json/wp/v2/pages/{HOME_PAGE_ID}",
    json={"content": content},
    timeout=30
)
print(f"  Page update: {r6.status_code}")
if r6.status_code != 200:
    print(f"  Error: {r6.text[:300]}")

print("\nDone! Please refresh the homepage and check if the feature blocks are centered.")
print("The CSS constrains feature blocks to 1100px max width with auto margins.")
