import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
AZURE = 'https://azure-nightingale-589250.hostingersite.com'
s = requests.Session()
s.auth = ('mikeoliveraz@gmail.com', 'vlop MpGU Os2V xDSI C6T7 2fAN')
r = s.get(f'{AZURE}/wp-json/wp/v2/pages',
          params={'per_page': 100, 'context': 'edit', '_fields': 'id,slug,title'},
          timeout=30)
pages = r.json()
for p in pages:
    title = p['title']['raw'] if isinstance(p['title'], dict) else p['title']
    print(f"  {p['id']:5d}  {p['slug']:40s}  {title}")

# Also get gallery-videos content
r2 = s.get(f'{AZURE}/wp-json/wp/v2/pages',
           params={'slug': 'gallery-videos', 'context': 'edit', '_fields': 'id,content'},
           timeout=30)
if r2.json():
    gv = r2.json()[0]
    print(f"\n=== Gallery Videos page (ID {gv['id']}) ===")
    print(gv['content']['raw'][:2000])
else:
    print("\nGallery Videos page not found")
