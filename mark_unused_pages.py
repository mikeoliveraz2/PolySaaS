"""
Set 5 blank pages to Draft status so they don't appear on the live site.
"""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,title,status"
}).json()

BLANK_SLUGS = [
    "cta-templates",
    "external-applications",
    "for-parners-resellers-and-large-enterprises",
    "for-resellers-of-liferay-and-django-customization",
    "sign-up",
]

for p in pages:
    if p['slug'] in BLANK_SLUGS:
        title = p['title']['raw'] if isinstance(p['title'], dict) else p['title']
        r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{p['id']}", json={
            "status": "draft"
        })
        print(f"  {p['slug']} (id={p['id']}): set to DRAFT - {r.status_code}")
