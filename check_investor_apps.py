"""Check investor page for application names and find available logos."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get investor page content
r = requests.get(BASE + "/wp-json/wp/v2/pages/2565",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# Find application names in the investor page
# Look for app-related headings or lists
app_names = ['Odoo', 'Nextcloud', 'Mattermost', 'WordPress', 'Liferay', 'Dolibarr', 'Monitor Logger', 'PolySysMon']

print("=== Application mentions in investor page ===")
for app in app_names:
    count = content.count(app)
    if count > 0:
        pos = content.find(app)
        context = content[max(0,pos-100):pos+100]
        # Clean HTML tags for readability
        clean = re.sub(r'<[^>]+>', ' ', context).strip()
        print(f"  {app}: {count}x | ...{clean[:150]}...")

# Find available logo images in the media library
print("\n=== Searching media library for app logos ===")
r2 = requests.get(BASE + "/wp-json/wp/v2/media",
                  params={"per_page": 100, "search": "logo", "_fields": "id,title,source_url,alt_text"},
                  auth=AUTH, timeout=30)
if r2.status_code == 200:
    media = r2.json()
    for m in media:
        print(f"  ID {m['id']}: {m['title']['rendered']} | {m['source_url']}")

# Also check for app-specific images
print("\n=== App-specific images ===")
for app in ['odoo', 'nextcloud', 'mattermost', 'wordpress', 'liferay', 'dolibarr', 'monitor', 'polysysmon']:
    r3 = requests.get(BASE + "/wp-json/wp/v2/media",
                      params={"per_page": 5, "search": app, "_fields": "id,title,source_url"},
                      auth=AUTH, timeout=15)
    if r3.status_code == 200:
        for m in r3.json():
            src = m['source_url']
            if any(ext in src.lower() for ext in ['.png', '.jpg', '.svg', '.webp']):
                print(f"  {app}: {m['title']['rendered']} | {src}")
