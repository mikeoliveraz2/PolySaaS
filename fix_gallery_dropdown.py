"""
Make Gallery a dropdown menu with Images and Videos sub-items.
"""
import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Menu 18: Gallery item id=1797
# Menu 21: Gallery item id=1789

# Step 1: Update Gallery items to be dropdown parents (url = #)
for item_id, menu_label in [(1797, "Menu 18"), (1789, "Menu 21")]:
    r = s.post(f"{AZURE}/wp-json/wp/v2/menu-items/{item_id}", json={
        "url": "#",
        "title": "Gallery"
    })
    if r.status_code == 200:
        print(f"{menu_label}: Gallery (id={item_id}) set to dropdown parent (url=#)")
    else:
        print(f"{menu_label}: FAILED to update Gallery item: {r.status_code}")
        print(r.text[:300])

# Step 2: Create "Images" and "Videos" sub-items under each Gallery parent
IMAGES_URL = f"{AZURE}/gallery-images/"
VIDEOS_URL = f"{AZURE}/gallery-videos/"

# For Menu 18 (id=18, parent gallery=1797)
for title, url in [("Images", IMAGES_URL), ("Videos", VIDEOS_URL)]:
    r = s.post(f"{AZURE}/wp-json/wp/v2/menu-items", json={
        "title": title,
        "url": url,
        "status": "publish",
        "menus": 18,
        "parent": 1797,
        "type": "custom",
    })
    if r.status_code == 201:
        print(f"Menu 18: Created '{title}' sub-item (id={r.json()['id']})")
    else:
        print(f"Menu 18: FAILED to create '{title}': {r.status_code}")
        print(r.text[:300])

# For Menu 21 (id=21, parent gallery=1789)
for title, url in [("Images", IMAGES_URL), ("Videos", VIDEOS_URL)]:
    r = s.post(f"{AZURE}/wp-json/wp/v2/menu-items", json={
        "title": title,
        "url": url,
        "status": "publish",
        "menus": 21,
        "parent": 1789,
        "type": "custom",
    })
    if r.status_code == 201:
        print(f"Menu 21: Created '{title}' sub-item (id={r.json()['id']})")
    else:
        print(f"Menu 21: FAILED to create '{title}': {r.status_code}")
        print(r.text[:300])

# Verify
print("\n--- Verification ---")
for menu_id in [18, 21]:
    r2 = s.get(f"{AZURE}/wp-json/wp/v2/menu-items", params={
        "menus": menu_id, "per_page": 100, "context": "edit"
    })
    if r2.status_code == 200:
        items = r2.json()
        print(f"\nMenu {menu_id}:")
        for item in sorted(items, key=lambda x: x.get('menu_order', 0)):
            title = item['title']['raw'] if isinstance(item['title'], dict) else item['title']
            parent = item.get('parent', 0)
            indent = "    " if parent else "  "
            print(f"{indent}id={item['id']} parent={parent} \"{title}\" -> {item.get('url', '')}")
