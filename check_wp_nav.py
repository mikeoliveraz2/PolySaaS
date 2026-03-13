import requests

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"
s = requests.Session()
s.auth = (USER, APP_PASS)

# Get the full header menu (ID 28)
print("=== HEADER MENU (ID 28) - FULL CONTENT ===")
r = s.get(f"{SITE}/wp-json/wp/v2/navigation/28")
if r.status_code == 200:
    nav = r.json()
    print(f"Title: {nav['title']['rendered']}")
    print(f"Status: {nav['status']}")
    content = nav.get('content', {}).get('rendered', '')
    print(f"\nRendered HTML:\n{content}")
    raw = nav.get('content', {}).get('raw', '')
    if raw:
        print(f"\nRaw content:\n{raw}")
else:
    print(f"Status: {r.status_code}")

# Also check menu-items endpoint
print("\n\n=== MENU ITEMS (wp/v2/menu-items) ===")
r2 = s.get(f"{SITE}/wp-json/wp/v2/menu-items", params={"per_page": 50, "menus": 28})
print(f"Status: {r2.status_code}")
if r2.status_code == 200:
    items = r2.json()
    print(f"Found {len(items)} items")
    for item in items:
        title = item.get('title', {})
        if isinstance(title, dict):
            title = title.get('rendered', '?')
        print(f"  [{item['id']}] {title} -> {item.get('url', '?')} (status={item.get('status')})")
elif r2.status_code == 401:
    print("  (auth required or endpoint not available)")
    print(f"  {r2.text[:300]}")
else:
    print(f"  {r2.text[:500]}")

# Fetch the actual front page HTML and extract nav links
print("\n\n=== ACTUAL NAV LINKS FROM FRONT PAGE HTML ===")
r3 = requests.get(SITE)
if r3.status_code == 200:
    import re
    # Find all nav links
    nav_links = re.findall(r'<a[^>]*class="[^"]*navigation-item[^"]*"[^>]*href="([^"]*)"[^>]*>.*?<span[^>]*class="[^"]*label[^"]*"[^>]*>(.*?)</span>', r3.text, re.DOTALL)
    if nav_links:
        for href, label in nav_links:
            label = re.sub(r'<[^>]+>', '', label).strip()
            print(f"  {label} -> {href}")
    else:
        # Try broader pattern
        nav_section = re.findall(r'<nav[^>]*>(.*?)</nav>', r3.text, re.DOTALL)
        for i, nav in enumerate(nav_section):
            links = re.findall(r'href="([^"]*)"[^>]*>(.*?)</a>', nav, re.DOTALL)
            if links:
                print(f"  Nav section {i+1}:")
                for href, text in links:
                    text = re.sub(r'<[^>]+>', '', text).strip()
                    if text:
                        print(f"    {text} -> {href}")
