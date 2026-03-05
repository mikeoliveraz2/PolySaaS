"""Check how the custom_css was stored and fix delivery."""
import requests
import re
import json

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

session = requests.Session()
session.auth = (USER, APP_PASS)

# Find the custom_css post
print("Looking for custom_css posts...")
# custom_css is a special post type, try different approaches

# Approach 1: Query with type parameter
resp = session.get(f"{SITE}/wp-json/wp/v2/posts", params={
    "per_page": 5,
    "orderby": "date",
    "order": "desc",
})
if resp.status_code == 200:
    posts = resp.json()
    for p in posts:
        print(f"  Post {p['id']}: {p.get('title', {}).get('rendered', '?')} [type: {p.get('type', '?')}]")

# Check what's in the rendered HTML — find the custom CSS style block
print("\nChecking rendered Home HTML for custom CSS...")
resp2 = requests.get(f"{SITE}/", headers={'User-Agent': 'PolySaaS-Verify/1.0'}, timeout=15)
html = resp2.text

# Look for where our CSS comment appears
idx = html.find('PolySaaS Site-Wide Brand Uniformity CSS')
if idx >= 0:
    # Get surrounding context (500 chars before and after)
    start = max(0, idx - 200)
    end = min(len(html), idx + 500)
    context = html[start:end]
    print(f"  Found at char {idx}. Context:")
    print(f"  ---")
    print(context[:600])
    print(f"  ---")
else:
    print("  Comment not found in rendered HTML")

# Look for any <style> tag with our content
style_blocks = re.findall(r'<style[^>]*id="[^"]*custom[^"]*"[^>]*>(.*?)</style>', html, re.DOTALL)
if style_blocks:
    print(f"\n  Found {len(style_blocks)} custom style blocks:")
    for i, block in enumerate(style_blocks):
        print(f"    Block {i}: {len(block)} chars")
        print(f"    Preview: {block[:300]}...")
else:
    print("\n  No custom style blocks found by ID pattern")
    # Look for any style block containing 'brxe'
    all_styles = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
    for i, block in enumerate(all_styles):
        if 'PolySaaS' in block or 'Brand Uniformity' in block:
            print(f"\n  Found our CSS in style block {i} ({len(block)} chars):")
            print(f"    Preview: {block[:400]}...")

# The issue is probably that the CSS got stored with HTML entities
# or wrapped in post content tags. Let's check the actual custom_css
# post via API by looking at the raw endpoint

# The WordPress Customizer stores custom CSS as a post with
# type = 'custom_css' and post_name = {theme_stylesheet}
# Let's try the special endpoint

# First, get the bricks theme stylesheet
resp3 = session.get(f"{SITE}/wp-json/wp/v2/themes")
if resp3.status_code == 200:
    for t in resp3.json():
        if t.get('status') == 'active':
            stylesheet = t.get('stylesheet', '')
            print(f"\n  Active theme stylesheet: {stylesheet}")

# Try reading global-styles or wp:custom-css
# In newer WordPress, try: /wp-json/wp/v2/global-styles
print("\nLooking for custom_css via REST routes...")
routes = session.get(f"{SITE}/wp-json/wp/v2/")
if routes.status_code == 200:
    route_list = routes.json()
    for key in sorted(route_list.keys()):
        if 'css' in key.lower() or 'style' in key.lower() or 'custom' in key.lower():
            print(f"  Route: {key}")

# Try to find the custom_css post by looking up post ID we created
# We got 201 which means a new post was created. Let's see recent posts of all types
print("\nSearching for recent custom_css posts by title...")
resp4 = session.get(f"{SITE}/wp-json/wp/v2/posts", params={
    "search": "bricks",
    "per_page": 10,
    "status": "any",
})
if resp4.status_code == 200:
    for p in resp4.json():
        print(f"  Found: ID={p['id']}, title='{p.get('title',{}).get('rendered','')}', "
              f"type={p.get('type','')}, status={p.get('status','')}")
        if 'bricks' in str(p.get('title',{}).get('rendered','')).lower():
            content = p.get('content', {}).get('rendered', '')
            print(f"    Content preview: {content[:200]}")
