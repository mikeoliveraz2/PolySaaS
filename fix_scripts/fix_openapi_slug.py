"""Fix OpenAPI page: change slug to 'openapi' and update homepage link."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# First check if there's an old page at /openapi/ we need to remove/rename
# Search all post types
for pt in ['pages', 'posts']:
    r = requests.get(BASE + f"/wp-json/wp/v2/{pt}",
                     params={"slug": "openapi", "_fields": "id,title,slug,status,type", "status": "any"},
                     auth=AUTH, timeout=30)
    if r.status_code == 200 and r.json():
        for p in r.json():
            print(f"Found {pt}: ID {p['id']}, title: {p.get('title',{}).get('rendered','')}, slug: {p['slug']}, status: {p['status']}")

# Also check if /openapi/ might be a custom rewrite or something
# Let's just try to change the real page's slug
print("\n--- Changing page 1640 slug from 'openapi-2' to 'openapi-swagger' first ---")
# If 'openapi' is taken, use 'openapi-swagger'
r2 = requests.post(BASE + "/wp-json/wp/v2/pages/1640",
                   auth=AUTH,
                   json={"slug": "openapi-swagger"},
                   timeout=30)
print(f"Slug change: {r2.status_code}")
if r2.status_code == 200:
    new_slug = r2.json().get("slug")
    print(f"New slug: {new_slug}")

# Now update the homepage Learn More link for OpenAPI
print("\n--- Updating homepage OpenAPI link ---")
r3 = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                  params={"context": "edit", "_fields": "content"},
                  auth=AUTH, timeout=45)
content = r3.json()["content"]["raw"]

# Find and replace the OpenAPI link
# The link is likely /openapi/ in an href
old_link = 'href="/openapi/"'
new_link = 'href="/openapi-swagger/"'

count = content.count(old_link)
print(f"Found {count} occurrences of {old_link}")

if count > 0:
    new_content = content.replace(old_link, new_link)
    r4 = requests.post(BASE + "/wp-json/wp/v2/pages/1313",
                       auth=AUTH,
                       json={"content": new_content},
                       timeout=45)
    print(f"Homepage update: {r4.status_code}")
    if r4.status_code == 200:
        print("SUCCESS - Homepage OpenAPI link now points to /openapi-swagger/")
else:
    # Try other link formats
    for pattern in ['/openapi/', 'openapi-2', '/openapi"']:
        c = content.count(pattern)
        if c > 0:
            print(f"  Found {c}x: {pattern}")

# Also update the footer link on the OpenAPI page itself
print("\n--- Checking OpenAPI page footer link ---")
r5 = requests.get(BASE + "/wp-json/wp/v2/pages/1640",
                  params={"context": "edit", "_fields": "content"},
                  auth=AUTH, timeout=45)
oc = r5.json()["content"]["raw"]
if '/openapi-2/' in oc:
    oc2 = oc.replace('/openapi-2/', '/openapi-swagger/')
    r6 = requests.post(BASE + "/wp-json/wp/v2/pages/1640",
                       auth=AUTH,
                       json={"content": oc2},
                       timeout=45)
    print(f"Self-link fix: {r6.status_code}")

# Verify
print("\n--- Verification ---")
r7 = requests.get(BASE + "/openapi-swagger/", timeout=30)
print(f"/openapi-swagger/ status: {r7.status_code}")
if r7.status_code == 200:
    for check in ['Standardized API', 'Key Capabilities']:
        print(f"  {'OK' if check in r7.text else 'MISSING'}: {check}")
