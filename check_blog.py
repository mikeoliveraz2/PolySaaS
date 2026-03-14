"""Check blog page status"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Check pages for blog
r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,title,content,status"
})
for p in r.json():
    if 'blog' in p['slug'].lower():
        title = p['title']['raw'] if isinstance(p['title'], dict) else p['title']
        raw = p['content']['raw']
        print(f"Page: {p['slug']} (id={p['id']}, status={p['status']})")
        print(f"  Title: {title}")
        print(f"  Content length: {len(raw)}")
        text = re.sub(r'<[^>]+>', ' ', raw)
        text = re.sub(r'\s+', ' ', text).strip()
        print(f"  Text: {text[:300]}")
        print()

# Check posts
r2 = s.get(f"{AZURE}/wp-json/wp/v2/posts", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,title,status,date"
})
posts = r2.json()
print(f"\nFound {len(posts)} blog posts:")
for p in posts:
    title = p['title']['raw'] if isinstance(p['title'], dict) else p['title']
    print(f"  {p['slug']} - \"{title}\" (status={p['status']}, date={p['date']})")

# Check what the Blog nav link points to
r3 = s.get(f"{AZURE}/wp-json/wp/v2/menu-items", params={"menus": 18, "per_page": 50})
if r3.status_code == 200:
    for item in r3.json():
        if 'blog' in item.get('title', {}).get('rendered', '').lower():
            print(f"\nNav menu item: {item['title']['rendered']} -> {item.get('url', 'no url')}")
