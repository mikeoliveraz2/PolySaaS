import requests
import re
import json
import os

WP_URL = "https://azure-nightingale-589250.hostingersite.com"
WP_USER = os.environ.get("WP_USER", "admin")
WP_PASS = os.environ.get("WP_PASS", "")

# 1. Find logo references on the home page
print("=== LOGO REFERENCES ON HOME PAGE ===")
r = requests.get(WP_URL, timeout=30)
html = r.text

logos = re.findall(r'(?:src|href)=["\']([^"\']*logo[^"\']*)["\']', html, re.IGNORECASE)
for l in logos:
    print(f"  {l}")

print("\n=== ALL IMG TAGS (first 30) ===")
imgs = re.findall(r'<img[^>]*src=["\']([^"\']+)["\'][^>]*>', html)
for i in imgs[:30]:
    print(f"  {i}")

# 2. Check site identity / customizer settings via REST API
print("\n=== SITE SETTINGS (site_logo, site_icon) ===")
try:
    r2 = requests.get(f"{WP_URL}/wp-json/wp/v2/settings", auth=(WP_USER, WP_PASS), timeout=15)
    if r2.status_code == 200:
        settings = r2.json()
        print(f"  site_logo: {settings.get('site_logo')}")
        print(f"  site_icon: {settings.get('site_icon')}")
    else:
        print(f"  Settings API returned {r2.status_code}")
except Exception as e:
    print(f"  Error: {e}")

# 3. Check media library for existing logo uploads
print("\n=== MEDIA LIBRARY: logo-related images ===")
try:
    r3 = requests.get(f"{WP_URL}/wp-json/wp/v2/media", params={"search": "logo", "per_page": 20},
                       auth=(WP_USER, WP_PASS), timeout=15)
    if r3.status_code == 200:
        for m in r3.json():
            print(f"  ID={m['id']}  slug={m.get('slug','')}  url={m.get('source_url','')}")
    else:
        print(f"  Media API returned {r3.status_code}")
except Exception as e:
    print(f"  Error: {e}")

# 4. Check a few inner pages for logo references
print("\n=== LOGO REFERENCES ON INNER PAGES ===")
for page in ["/architecture/", "/sign-up/", "/schedule-demo/"]:
    try:
        rp = requests.get(f"{WP_URL}{page}", timeout=15)
        page_logos = re.findall(r'(?:src|href)=["\']([^"\']*logo[^"\']*)["\']', rp.text, re.IGNORECASE)
        if page_logos:
            print(f"  {page}:")
            for pl in page_logos:
                print(f"    {pl}")
        else:
            print(f"  {page}: no logo refs found")
    except Exception as e:
        print(f"  {page}: error - {e}")
