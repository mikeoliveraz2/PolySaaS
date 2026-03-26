"""Check About Us page structure and fix white gaps on sides."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# First find the About Us page
r = requests.get(BASE + "/wp-json/wp/v2/pages",
                 params={"search": "About", "_fields": "id,title,slug,status"},
                 auth=AUTH, timeout=30)
pages = r.json()
for p in pages:
    print(f"ID: {p['id']}, Title: {p['title']['rendered']}, Slug: {p['slug']}, Status: {p['status']}")
