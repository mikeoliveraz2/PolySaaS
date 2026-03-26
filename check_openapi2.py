"""Check the OpenAPI/Swagger page (ID 1640) content."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get the OpenAPI page content (ID 1640)
r = requests.get(f"{BASE}/wp-json/wp/v2/pages/1640?context=edit&_fields=content,title,slug",
                 auth=AUTH, timeout=15)
page = r.json()
print(f"Title: {page['title']['raw']}")
print(f"Slug: {page['slug']}")
content = page['content']['raw']
print(f"Content length: {len(content)} chars")
print(f"\n=== Full content ===")
print(content)
