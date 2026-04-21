"""Set the Blog page (ID 1347) as the posts page in WordPress settings."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.post(BASE + "/wp-json/wp/v2/settings",
                  auth=AUTH,
                  json={"page_for_posts": 1347},
                  timeout=30)
print(f"Update settings: {r.status_code}")
if r.status_code == 200:
    settings = r.json()
    print(f"page_for_posts now: {settings.get('page_for_posts')}")
    print("SUCCESS - Blog page (ID 1347) is now the posts page")
else:
    print(f"Error: {r.text[:300]}")
