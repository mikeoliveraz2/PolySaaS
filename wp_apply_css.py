"""Apply the updated CSS to WordPress Customizer Additional CSS."""
import requests
import json

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

session = requests.Session()
session.auth = (USER, APP_PASS)

with open("PASTE_THIS_CSS.css", "r") as f:
    css_content = f.read()

# Try method 1: Find the active custom_css post for the current theme
print("=== Method 1: Find and update custom_css post ===")
r = session.get(f"{SITE}/wp-json/wp/v2/themes", params={"status": "active"})
if r.status_code == 200 and r.json():
    theme = r.json()[0]
    theme_slug = theme.get("stylesheet", "")
    print(f"  Active theme: {theme_slug}")

    # Search for custom_css post type
    r2 = session.get(f"{SITE}/wp-json/wp/v2/posts",
                     params={"type": "custom_css", "per_page": 50})
    if r2.status_code == 200:
        print(f"  Found {len(r2.json())} custom_css posts")
    else:
        print(f"  custom_css via posts: {r2.status_code}")
else:
    print(f"  Themes API: {r.status_code}")
    theme_slug = ""

# Try method 2: Direct custom CSS endpoint
print("\n=== Method 2: Try wp/v2/custom-css ===")
for endpoint in ["custom-css", "custom_css"]:
    r = session.get(f"{SITE}/wp-json/wp/v2/{endpoint}")
    print(f"  /wp/v2/{endpoint}: {r.status_code}")
    if r.status_code == 200:
        print(f"    Response: {r.text[:300]}")

# Try method 3: Global Styles API
print("\n=== Method 3: Check global styles ===")
r = session.get(f"{SITE}/wp-json/wp/v2/global-styles")
if r.status_code == 200:
    styles = r.json()
    print(f"  Found {len(styles)} global style entries")
    for s in styles:
        print(f"    ID={s.get('id')} title={s.get('title',{}).get('rendered','')}")
else:
    print(f"  Global styles: {r.status_code}")

# Try method 4: Search for any post with custom_css type via generic search
print("\n=== Method 4: Search for custom CSS in all post types ===")
for post_type in ["custom_css"]:
    r = session.get(f"{SITE}/wp-json/wp/v2/types/{post_type}")
    if r.status_code == 200:
        type_info = r.json()
        rest_base = type_info.get("rest_base", "")
        print(f"  custom_css type exists, rest_base='{rest_base}'")
        if rest_base:
            r2 = session.get(f"{SITE}/wp-json/wp/v2/{rest_base}", params={"per_page": 50})
            print(f"    {rest_base}: {r2.status_code}")
            if r2.status_code == 200:
                for item in r2.json():
                    print(f"      ID={item['id']} content_preview={str(item.get('content',{}))[:200]}")
    else:
        print(f"  custom_css type: {r.status_code}")

# Try method 5: Use the WordPress Customizer changeset API
print("\n=== Method 5: Try changeset approach ===")
# Create a changeset with custom CSS
changeset_data = {
    f"custom_css[{theme_slug}]": {
        "value": css_content,
        "type": "custom_css",
    }
}
r = session.post(f"{SITE}/wp-json/customize/v1/changesets",
                 json=changeset_data)
print(f"  Changeset API: {r.status_code}")
if r.status_code in [200, 201]:
    print(f"  Response: {r.text[:300]}")

# Try method 6: Options API
print("\n=== Method 6: Try settings/options for custom CSS ===")
r = session.get(f"{SITE}/wp-json/wp/v2/settings")
if r.status_code == 200:
    settings = r.json()
    for key in settings:
        if 'css' in key.lower() or 'custom' in key.lower() or 'style' in key.lower():
            print(f"  {key}: {str(settings[key])[:200]}")

print("\n=== DONE ===")
