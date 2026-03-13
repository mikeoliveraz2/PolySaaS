import requests

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"
s = requests.Session()
s.auth = (USER, APP_PASS)

# Check the blog page (ID 1347 from bingo doc)
print("=== BLOG PAGE (ID 1347) ===")
r = s.get(f"{SITE}/wp-json/wp/v2/pages/1347")
if r.status_code == 200:
    page = r.json()
    print(f"  Title: {page['title']['rendered']}")
    print(f"  Status: {page['status']}")
    print(f"  Slug: {page['slug']}")
    print(f"  Link: {page['link']}")
    print(f"  Template: {page.get('template', 'default')}")
else:
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.text[:300]}")

# Check all pages with 'blog' in slug or title
print("\n=== ALL PAGES WITH 'BLOG' ===")
r2 = s.get(f"{SITE}/wp-json/wp/v2/pages", params={"per_page": 100, "search": "blog"})
if r2.status_code == 200:
    for p in r2.json():
        print(f"  [{p['id']}] {p['title']['rendered']} | status={p['status']} | slug={p['slug']} | link={p['link']}")
else:
    print(f"  Status: {r2.status_code}")

# Check WordPress reading settings (what's the posts page?)
print("\n=== SITE SETTINGS ===")
r3 = s.get(f"{SITE}/wp-json/wp/v2/settings")
if r3.status_code == 200:
    settings = r3.json()
    print(f"  show_on_front: {settings.get('show_on_front', '?')}")
    print(f"  page_on_front: {settings.get('page_on_front', '?')}")
    print(f"  page_for_posts: {settings.get('page_for_posts', '?')}")
else:
    print(f"  Status: {r3.status_code}")

# Check menus via wp/v2/navigation
print("\n=== NAVIGATION MENUS ===")
r4 = s.get(f"{SITE}/wp-json/wp/v2/navigation", params={"per_page": 50})
if r4.status_code == 200:
    for nav in r4.json():
        print(f"  [{nav['id']}] {nav['title']['rendered']} | status={nav['status']}")
        content = nav.get('content', {}).get('rendered', '')
        if content:
            print(f"    Content preview: {content[:500]}")
else:
    print(f"  Status: {r4.status_code}")

# Try fetching the blog URL directly
print("\n=== BLOG URL CHECK ===")
for url in ["/blog/", "/blog", "/Blog/", "/Blog"]:
    full = SITE + url
    r5 = requests.get(full, allow_redirects=False)
    print(f"  {url} -> status={r5.status_code}, location={r5.headers.get('Location', 'none')}")
