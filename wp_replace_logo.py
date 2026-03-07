import requests
import re
import json
import os

WP_URL = "https://azure-nightingale-589250.hostingersite.com"
WP_USER = os.environ.get("WP_USER", "admin")
WP_PASS = os.environ.get("WP_PASS", "")

OLD_LOGO_URL = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2025/12/Industrial-PolySaas-Cropped-300-Transparent.png"
NEW_LOGO_URL = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/ezgif-logo-final.gif"
NEW_LOGO_ID = 1723

OLD_LOGO_PATTERNS = [
    "Industrial-PolySaas-Cropped-300-Transparent",
    "Industrial-PolySaas-Logo-Transparent",
    "PolySaaS-Industrial-Logo-BIG",
    "cropped-Industrial-PolySaas-Cropped-300-Transparent",
]

auth = (WP_USER, WP_PASS)

# Step 1: Get all pages and check which ones reference old logos
print("=== SCANNING ALL PAGES FOR OLD LOGO REFERENCES ===")
pages_to_update = []
page_offset = 1
while True:
    r = requests.get(f"{WP_URL}/wp-json/wp/v2/pages",
                     params={"per_page": 50, "page": page_offset, "status": "publish,draft"},
                     auth=auth, timeout=15)
    if r.status_code != 200 or not r.json():
        break
    for page in r.json():
        content = page.get("content", {}).get("rendered", "")
        raw_content = json.dumps(page)
        found_patterns = []
        for pat in OLD_LOGO_PATTERNS:
            if pat in raw_content:
                found_patterns.append(pat)
        if found_patterns:
            pages_to_update.append({
                "id": page["id"],
                "title": page.get("title", {}).get("rendered", ""),
                "slug": page.get("slug", ""),
                "patterns": found_patterns,
            })
            print(f"  Page ID={page['id']} '{page.get('title',{}).get('rendered','')}' -> {found_patterns}")
    page_offset += 1

if not pages_to_update:
    print("  No pages found with old logo references in content.")

# Step 2: Check posts too
print("\n=== SCANNING POSTS ===")
posts_to_update = []
post_offset = 1
while True:
    r = requests.get(f"{WP_URL}/wp-json/wp/v2/posts",
                     params={"per_page": 50, "page": post_offset},
                     auth=auth, timeout=15)
    if r.status_code != 200 or not r.json():
        break
    for post in r.json():
        raw_content = json.dumps(post)
        found_patterns = []
        for pat in OLD_LOGO_PATTERNS:
            if pat in raw_content:
                found_patterns.append(pat)
        if found_patterns:
            posts_to_update.append({
                "id": post["id"],
                "title": post.get("title", {}).get("rendered", ""),
                "patterns": found_patterns,
            })
            print(f"  Post ID={post['id']} '{post.get('title',{}).get('rendered','')}' -> {found_patterns}")
    post_offset += 1

if not posts_to_update:
    print("  No posts found with old logo references.")

# Step 3: Try to update site_logo via settings
print("\n=== UPDATING SITE IDENTITY (site_logo) ===")
try:
    r_set = requests.post(f"{WP_URL}/wp-json/wp/v2/settings",
                          json={"site_logo": NEW_LOGO_ID, "site_icon": NEW_LOGO_ID},
                          auth=auth, timeout=15)
    if r_set.status_code == 200:
        result = r_set.json()
        print(f"  site_logo set to: {result.get('site_logo')}")
        print(f"  site_icon set to: {result.get('site_icon')}")
    else:
        print(f"  Settings update returned {r_set.status_code}: {r_set.text[:300]}")
except Exception as e:
    print(f"  Error: {e}")

# Step 4: Update page content where old logo is referenced
print("\n=== UPDATING PAGE CONTENT ===")
for page_info in pages_to_update:
    pid = page_info["id"]
    # Get the raw content
    r_page = requests.get(f"{WP_URL}/wp-json/wp/v2/pages/{pid}",
                          params={"context": "edit"},
                          auth=auth, timeout=15)
    if r_page.status_code != 200:
        print(f"  Page {pid}: could not fetch (status {r_page.status_code})")
        continue

    page_data = r_page.json()
    raw = page_data.get("content", {}).get("raw", "")
    if not raw:
        raw = page_data.get("content", {}).get("rendered", "")

    updated = raw
    for pat in OLD_LOGO_PATTERNS:
        # Replace any URL containing the old logo pattern with the new logo URL
        updated = re.sub(
            r'https?://[^"\'\s]*' + re.escape(pat) + r'[^"\'\s]*\.(png|jpg|jpeg|gif|webp)',
            NEW_LOGO_URL,
            updated
        )

    if updated != raw:
        r_up = requests.post(f"{WP_URL}/wp-json/wp/v2/pages/{pid}",
                             json={"content": updated},
                             auth=auth, timeout=15)
        if r_up.status_code == 200:
            print(f"  Page {pid} '{page_info['title']}' -> UPDATED")
        else:
            print(f"  Page {pid} '{page_info['title']}' -> FAILED ({r_up.status_code})")
    else:
        print(f"  Page {pid} '{page_info['title']}' -> no content change needed (logo may be in Bricks data)")

# Step 5: Check for Bricks-specific data
print("\n=== CHECKING BRICKS TEMPLATE DATA ===")
# Bricks stores page content in post meta '_bricks_page_content_2'
# We need to check this for each page
for page_info in pages_to_update:
    pid = page_info["id"]
    print(f"  Page {pid} '{page_info['title']}' has old logo patterns in Bricks data - need manual Bricks update or meta API")

# Also scan all pages for Bricks meta that might contain the logo
print("\n=== SCANNING ALL PAGES FOR BRICKS LOGO REFERENCES ===")
page_offset = 1
bricks_pages = []
while True:
    r = requests.get(f"{WP_URL}/wp-json/wp/v2/pages",
                     params={"per_page": 50, "page": page_offset, "status": "publish,draft"},
                     auth=auth, timeout=15)
    if r.status_code != 200 or not r.json():
        break
    for page in r.json():
        # Fetch rendered HTML to check for logo
        slug = page.get("slug", "")
        pid = page["id"]
        title = page.get("title", {}).get("rendered", "")
        try:
            rp = requests.get(f"{WP_URL}/?page_id={pid}", timeout=15)
            for pat in OLD_LOGO_PATTERNS:
                if pat in rp.text:
                    bricks_pages.append({"id": pid, "title": title, "slug": slug})
                    print(f"  Page {pid} '{title}' (/{slug}/) has old logo in rendered HTML")
                    break
        except:
            pass
    page_offset += 1

if not bricks_pages:
    print("  No additional Bricks pages found with old logo in rendered HTML.")

# Step 6: Check the Bricks global header template
print("\n=== CHECKING FOR BRICKS TEMPLATES (custom post type) ===")
for cpt in ["bricks_template", "wp_template", "wp_template_part"]:
    try:
        r_t = requests.get(f"{WP_URL}/wp-json/wp/v2/{cpt}",
                           params={"per_page": 50},
                           auth=auth, timeout=15)
        if r_t.status_code == 200:
            templates = r_t.json()
            for t in templates:
                raw_t = json.dumps(t)
                for pat in OLD_LOGO_PATTERNS:
                    if pat in raw_t:
                        print(f"  Template type={cpt} ID={t['id']} title={t.get('title',{}).get('rendered','')} has old logo")
                        break
        else:
            print(f"  {cpt}: API returned {r_t.status_code}")
    except Exception as e:
        print(f"  {cpt}: error - {e}")

print("\n=== DONE ===")
