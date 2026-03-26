"""Add small app logos to each application card on the investor page."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get all 8 app logos from the homepage - need a bigger section
r = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
homepage = r.json()["content"]["raw"]

# Find the full app section
app_start = homepage.find('Eight Enterprise-Grade')
app_end = homepage.find('All Your Applications', app_start)
app_section = homepage[app_start:app_end] if app_end > app_start else homepage[app_start:app_start+10000]

# Get all images with their nearby h3 headings
imgs = re.findall(r'<img[^>]+src="([^"]+)"[^>]*/?>.*?<h3[^>]*>([^<]+)</h3>', app_section, re.DOTALL)
print("=== Homepage app images with names ===")
for img_url, name in imgs:
    print(f"  {name.strip()}: {img_url}")

# Map app names to logo URLs
# Use homepage logos where available, media library for the rest
logo_map = {
    'Odoo': 'https://polysaas.online/wp-content/uploads/2026/03/odoo-logo-icon.png',
    'Nextcloud': 'https://polysaas.online/wp-content/uploads/2026/02/NextCloud-Logo.png',
    'Mattermost': 'https://polysaas.online/wp-content/uploads/2026/03/mattermost-icon.png',
    'WordPress': 'https://polysaas.online/wp-content/uploads/2026/03/wordpress.jpg',
    'Liferay': 'https://polysaas.online/wp-content/uploads/2026/02/Liferay-Logo.png',
    'Dolibarr': 'https://polysaas.online/wp-content/uploads/2026/02/dolibarr-logo.png',
    'Monitor Logger': 'https://polysaas.online/wp-content/uploads/2026/03/monitor-logger-logo.png',
    'PolySysMon': 'https://polysaas.online/wp-content/uploads/2026/01/polysysmon-5.png',
}

# Override with homepage images where we found matches
for img_url, name in imgs:
    name = name.strip()
    if name in logo_map:
        logo_map[name] = img_url
        
print("\n=== Final logo map ===")
for name, url in logo_map.items():
    print(f"  {name}: {url}")

# Now get investor page and add logos
r2 = requests.get(BASE + "/wp-json/wp/v2/pages/2565",
                  params={"context": "edit", "_fields": "content"},
                  auth=AUTH, timeout=45)
inv_content = r2.json()["content"]["raw"]

# For each app, replace <h3>AppName</h3> with <h3><img ...> AppName</h3>
# The logo should be small (roughly same height as the text, ~24px)
changes = 0
for app_name, logo_url in logo_map.items():
    old_h3 = f'<h3>{app_name}</h3>'
    new_h3 = f'<h3><img src="{logo_url}" alt="{app_name}" style="width:24px;height:24px;object-fit:contain;vertical-align:middle;margin-right:8px;border-radius:4px">{app_name}</h3>'
    if old_h3 in inv_content:
        inv_content = inv_content.replace(old_h3, new_h3)
        changes += 1
        print(f"  Added logo for {app_name}")

print(f"\nTotal changes: {changes}")

if changes > 0:
    r3 = requests.post(BASE + "/wp-json/wp/v2/pages/2565",
                       auth=AUTH,
                       json={"content": inv_content},
                       timeout=45)
    print(f"Update: {r3.status_code}")
    if r3.status_code == 200:
        print("SUCCESS - App logos added to investor page")
    else:
        print(f"Error: {r3.text[:300]}")
else:
    print("No changes made - headings might have different format")
    # Debug: show what h3 tags look like
    h3s = re.findall(r'<h3[^>]*>(.*?)</h3>', inv_content)
    print("H3 tags in investor page:")
    for h in h3s[:15]:
        print(f"  {h[:80]}")
