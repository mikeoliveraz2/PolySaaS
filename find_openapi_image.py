"""
Search Azure media library for OpenAPI/Swagger screenshot.
"""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

for term in ['swagger', 'openapi', 'api']:
    media = s.get(f"{AZURE}/wp-json/wp/v2/media", params={
        "per_page": 50, "search": term, "_fields": "id,source_url,title"
    }).json()
    print(f"Search '{term}': {len(media)} results")
    for m in media:
        title = m['title']['rendered'] if isinstance(m['title'], dict) else m['title']
        print(f"  id={m['id']}: {title}")
        print(f"    {m['source_url']}")
