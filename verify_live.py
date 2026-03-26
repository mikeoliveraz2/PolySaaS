"""Verify PolySaaS.online is live and migration carried over our changes."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Check site is up
r = requests.get(BASE, timeout=30)
print(f"Site status: {r.status_code}")
print(f"HTML length: {len(r.text)}")

html = r.text

# Verify key content migrated
checks = [
    ('Platform Features', 'Platform Features section'),
    ('platform-features', 'Platform Features anchor'),
    ('Francis Uy', 'Francis Uy advisor'),
    ('justify-content: center', 'Feature centering CSS'),
    ('max-width: 48%', 'Feature 48% columns'),
    ('WP Mail SMTP', 'SMTP plugin reference'),
    ('Sign Up', 'Sign Up page link'),
]

print("\n=== Migration verification ===")
for pattern, desc in checks:
    found = pattern in html
    print(f"  {'OK' if found else 'MISSING'}: {desc}")

# Check REST API access
r2 = requests.get(f"{BASE}/wp-json/wp/v2/pages?per_page=5&_fields=id,title,status",
                  auth=AUTH, timeout=15)
print(f"\nREST API: {r2.status_code}")
if r2.status_code == 200:
    pages = r2.json()
    print(f"Pages accessible: {len(pages)}")
    for p in pages:
        print(f"  ID {p['id']}: {p['title']['rendered']} ({p['status']})")
elif r2.status_code == 401:
    print("Auth failed - may need new application password for polysaas.online")
