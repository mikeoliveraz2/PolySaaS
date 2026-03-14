"""
Check Gallery pages and nav menu structure, then make Gallery a dropdown
with Images and Videos sub-items.
"""
import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Check pages
r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,title,status,link"
})
pages = r.json()
for p in pages:
    slug = p['slug']
    if any(x in slug.lower() for x in ['gallery', 'image', 'video']):
        title = p['title']['raw'] if isinstance(p['title'], dict) else p['title']
        print(f"Page: {slug} (id={p['id']}, status={p['status']})")
        print(f"  Title: {title}")
        print(f"  Link: {p.get('link', 'N/A')}")
        print()

# Check all menus and their items
print("=" * 60)
print("MENU ITEMS:")
for menu_id in [18, 21]:
    r2 = s.get(f"{AZURE}/wp-json/wp/v2/menu-items", params={
        "menus": menu_id, "per_page": 100, "context": "edit"
    })
    if r2.status_code == 200:
        items = r2.json()
        print(f"\nMenu {menu_id} ({len(items)} items):")
        for item in sorted(items, key=lambda x: x.get('menu_order', 0)):
            title = item['title']['raw'] if isinstance(item['title'], dict) else item['title']
            parent = item.get('parent', 0)
            url = item.get('url', 'N/A')
            print(f"  id={item['id']} parent={parent} order={item.get('menu_order',0)} \"{title}\" -> {url}")
