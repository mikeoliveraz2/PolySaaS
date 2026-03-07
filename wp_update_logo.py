"""Update the PolySaaS logo everywhere on the WordPress site."""
import requests
import re
import json

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

NEW_LOGO_URL = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/ezgif-logo-final.gif"
NEW_LOGO_ID = 1723

session = requests.Session()
session.auth = (USER, APP_PASS)

# Step 1: Update site_logo and site_icon in WordPress settings
print("=== Step 1: Update Site Identity (site_logo + site_icon) ===")
r = session.post(f"{SITE}/wp-json/wp/v2/settings",
                 json={"site_logo": NEW_LOGO_ID, "site_icon": NEW_LOGO_ID})
if r.status_code == 200:
    data = r.json()
    print(f"  site_logo -> {data.get('site_logo')}")
    print(f"  site_icon -> {data.get('site_icon')}")
else:
    print(f"  FAILED: {r.status_code} - {r.text[:300]}")

# Step 2: Scan all pages for old logo references in content
print("\n=== Step 2: Scan pages for old logo in content ===")
OLD_PATTERNS = [
    "Industrial-PolySaas-Cropped-300-Transparent",
    "Industrial-PolySaas-Logo-Transparent",
    "PolySaaS-Industrial-Logo-BIG",
]

page_num = 1
pages_updated = 0
while True:
    r = session.get(f"{SITE}/wp-json/wp/v2/pages",
                    params={"per_page": 50, "page": page_num, "context": "edit", "status": "publish,draft"})
    if r.status_code != 200 or not r.json():
        break
    for page in r.json():
        pid = page["id"]
        title = page.get("title", {}).get("raw", page.get("title", {}).get("rendered", f"ID {pid}"))
        raw_content = page.get("content", {}).get("raw", "")

        has_old = False
        for pat in OLD_PATTERNS:
            if pat in raw_content:
                has_old = True
                break

        if has_old:
            updated = raw_content
            for pat in OLD_PATTERNS:
                updated = re.sub(
                    r'https?://[^"\'\s<>]*' + re.escape(pat) + r'[^"\'\s<>]*\.(png|jpg|jpeg|gif|webp|avif)',
                    NEW_LOGO_URL,
                    updated
                )
            if updated != raw_content:
                r_up = session.post(f"{SITE}/wp-json/wp/v2/pages/{pid}",
                                   json={"content": updated})
                if r_up.status_code == 200:
                    print(f"  Page {pid} '{title}' -> UPDATED content")
                    pages_updated += 1
                else:
                    print(f"  Page {pid} '{title}' -> FAILED ({r_up.status_code})")
            else:
                print(f"  Page {pid} '{title}' -> pattern found but no URL match in raw content")
    page_num += 1

print(f"  Total pages with content updated: {pages_updated}")

# Step 3: Check and update Bricks template data via custom meta endpoint
print("\n=== Step 3: Check Bricks templates ===")
# Bricks stores data in post meta '_bricks_page_content_2'
# Try to access via custom REST endpoint or post meta
for cpt in ["bricks_template"]:
    r = session.get(f"{SITE}/wp-json/wp/v2/{cpt}", params={"per_page": 50})
    if r.status_code == 200:
        for tmpl in r.json():
            tid = tmpl["id"]
            tmpl_title = tmpl.get("title", {}).get("rendered", f"ID {tid}")
            raw_tmpl = json.dumps(tmpl)
            for pat in OLD_PATTERNS:
                if pat in raw_tmpl:
                    print(f"  Template {tid} '{tmpl_title}' contains old logo ref")
                    break
    else:
        print(f"  {cpt} endpoint: {r.status_code}")

# Step 4: Try to read Bricks meta for all pages
print("\n=== Step 4: Check Bricks page meta for logo references ===")
page_num = 1
bricks_pages_with_logo = []
while True:
    r = session.get(f"{SITE}/wp-json/wp/v2/pages",
                    params={"per_page": 50, "page": page_num, "context": "edit"})
    if r.status_code != 200 or not r.json():
        break
    for page in r.json():
        pid = page["id"]
        title = page.get("title", {}).get("raw", "")
        meta = page.get("meta", {})
        full_json = json.dumps(page)
        for pat in OLD_PATTERNS:
            if pat in full_json:
                bricks_pages_with_logo.append({"id": pid, "title": title})
                print(f"  Page {pid} '{title}' has old logo in full JSON (possibly Bricks meta)")
                break
    page_num += 1

# Step 5: Verify the new media item
print("\n=== Step 5: Verify new logo media item ===")
r = session.get(f"{SITE}/wp-json/wp/v2/media/{NEW_LOGO_ID}")
if r.status_code == 200:
    media = r.json()
    print(f"  ID: {media['id']}")
    print(f"  URL: {media.get('source_url')}")
    print(f"  MIME: {media.get('mime_type')}")
    sizes = media.get("media_details", {}).get("sizes", {})
    if sizes:
        print(f"  Sizes: {list(sizes.keys())}")
    else:
        print("  No generated sizes (expected for GIF)")
else:
    print(f"  Media {NEW_LOGO_ID}: {r.status_code}")

print("\n=== DONE ===")
