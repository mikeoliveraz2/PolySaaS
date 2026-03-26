"""Add small app logos next to application names on investor page."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# First, find the logo images used on the homepage app cards
r = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
homepage = r.json()["content"]["raw"]

# Find app card images - they're in the "Eight Enterprise-Grade Applications" section
# Each app has an img tag with class "app-logo" or similar
app_section_start = homepage.find('Eight Enterprise-Grade')
if app_section_start > 0:
    app_section = homepage[app_section_start:app_section_start+5000]
    imgs = re.findall(r'<img[^>]+src="([^"]+)"[^>]*>', app_section)
    print("=== App card images from homepage ===")
    for img in imgs:
        print(f"  {img}")

# Now get the investor page
r2 = requests.get(BASE + "/wp-json/wp/v2/pages/2565",
                  params={"context": "edit", "_fields": "content"},
                  auth=AUTH, timeout=45)
inv_content = r2.json()["content"]["raw"]

# Find the applications section - look for Odoo heading
apps_pos = inv_content.find('>Odoo<')
if apps_pos < 0:
    apps_pos = inv_content.find('Odoo')
print(f"\nOdoo found at position: {apps_pos}")

# Show the HTML structure around the app listings
if apps_pos > 0:
    start = max(0, apps_pos - 200)
    end = min(len(inv_content), apps_pos + 2000)
    print(f"\n=== Investor page app section ===")
    print(inv_content[start:end])
