import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
AZURE = 'https://azure-nightingale-589250.hostingersite.com'
s = requests.Session()
s.auth = ('mikeoliveraz@gmail.com', 'vlop MpGU Os2V xDSI C6T7 2fAN')

# Search for cross-app page
r = s.get(AZURE + '/wp-json/wp/v2/pages', params={
    'search': 'cross', 'context': 'edit', '_fields': 'id,slug,title,status,link',
    'per_page': 20
})
print("Search results:", r.status_code)
for p in r.json():
    print(f"  id={p['id']}  slug={p['slug']}  status={p['status']}  title={p['title']['raw']}")
    print(f"    link={p.get('link','N/A')}")

# Also check by slug directly
r2 = s.get(AZURE + '/wp-json/wp/v2/pages', params={
    'slug': 'cross-app-sync', 'context': 'edit', '_fields': 'id,slug,title,status,link',
    'status': 'publish,draft,private,pending,trash'
})
print("\nDirect slug lookup:", r2.status_code)
for p in r2.json():
    print(f"  id={p['id']}  slug={p['slug']}  status={p['status']}  title={p['title']['raw']}")

# Check page by ID 2615
r3 = s.get(AZURE + '/wp-json/wp/v2/pages/2615', params={'context': 'edit', '_fields': 'id,slug,title,status,link'})
print("\nPage 2615:", r3.status_code)
if r3.status_code == 200:
    p = r3.json()
    print(f"  id={p['id']}  slug={p['slug']}  status={p['status']}  title={p['title']['raw']}")
    print(f"  link={p.get('link','N/A')}")
else:
    print(f"  {r3.text[:300]}")
