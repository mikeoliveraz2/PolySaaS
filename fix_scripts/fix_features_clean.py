"""Remove test styling and apply clean centering to features section."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://azure-nightingale-589250.hostingersite.com"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get current content
r = requests.get(f"{BASE}/wp-json/wp/v2/pages/1313?context=edit&_fields=content",
                 auth=AUTH, timeout=30)
page = r.json()
content = page['content']['raw']

# Replace the test styling with clean centering
old = '<div class="wp-block-group" style="max-width:700px;margin:0 auto;padding-top:10px;padding-bottom:12px;background:red;border:5px solid yellow">'
new = '<div class="wp-block-group" style="max-width:900px;margin:0 auto;padding-top:10px;padding-bottom:12px">'

if old in content:
    new_content = content.replace(old, new)
    r2 = requests.post(
        f"{BASE}/wp-json/wp/v2/pages/1313",
        auth=AUTH,
        json={"content": new_content},
        timeout=30
    )
    print(f"Update: {r2.status_code}")
    if r2.status_code == 200:
        print("SUCCESS - Removed red/yellow, set clean 900px centered width")
    else:
        print(f"Error: {r2.text[:300]}")
else:
    print("Test wrapper not found!")
    if 'background:red' in content:
        print("  (background:red IS in content but wrapper string didn't match)")
