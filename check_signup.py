"""Check the Sign Up page content and WPForms configuration."""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get the Sign Up page content
r = s.get(f"{AZURE}/wp-json/wp/v2/pages",
          params={"slug": "sign-up", "context": "edit", "_fields": "id,title,content,status"},
          timeout=30)
if r.status_code == 200 and r.json():
    page = r.json()[0]
    print(f"Page ID: {page['id']}")
    print(f"Title: {page['title']['raw']}")
    print(f"Status: {page['status']}")
    print(f"\nRaw content:\n{page['content']['raw']}")
else:
    print(f"Error: {r.status_code} - {r.text[:300]}")

# Check WPForms entries/forms
print("\n\n=== Checking WPForms ===")
# Try kadence_form endpoint
r2 = s.get(f"{AZURE}/wp-json/wp/v2/kadence_form",
           params={"per_page": 20, "_fields": "id,title,status"},
           timeout=30)
print(f"Kadence forms: {r2.status_code}")
if r2.status_code == 200:
    for form in r2.json():
        print(f"  Form ID: {form['id']}, Title: {form.get('title', {}).get('rendered', 'N/A')}, Status: {form['status']}")

# Try WPForms REST endpoint
for ep in ['/wp-json/wpforms/v1/forms', '/wp-json/wpforms-lite/v1/forms']:
    r3 = s.get(f"{AZURE}{ep}", timeout=15)
    print(f"\n{ep}: {r3.status_code}")
    if r3.status_code == 200:
        print(f"  Data: {json.dumps(r3.json(), indent=2)[:1000]}")
