"""Check blog page and recent posts on polysaas.online."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get recent posts
r = requests.get(BASE + "/wp-json/wp/v2/posts",
                 params={"per_page": 10, "_fields": "id,title,status,date,link,slug"},
                 auth=AUTH, timeout=30)
posts = r.json()
print(f"=== {len(posts)} posts found ===\n")
for p in posts:
    print(f"  ID: {p['id']}, Status: {p['status']}, Date: {p['date']}")
    print(f"  Title: {p['title']['rendered']}")
    print(f"  Link: {p['link']}")
    print()

# Check the blog page
r2 = requests.get(BASE + "/wp-json/wp/v2/pages/1347",
                  params={"context": "edit", "_fields": "content,title,status"},
                  auth=AUTH, timeout=30)
page = r2.json()
print(f"=== Blog page (ID 1347) ===")
print(f"Title: {page['title']['raw']}")
print(f"Status: {page['status']}")
content = page['content']['raw']
print(f"Content length: {len(content)} chars")
print(f"First 500 chars:\n{content[:500]}")

# Check WordPress reading settings (what page is set as blog)
r3 = requests.get(BASE + "/wp-json/wp/v2/settings",
                  auth=AUTH, timeout=30)
if r3.status_code == 200:
    settings = r3.json()
    print(f"\n=== Site Settings ===")
    print(f"show_on_front: {settings.get('show_on_front')}")
    print(f"page_on_front: {settings.get('page_on_front')}")
    print(f"page_for_posts: {settings.get('page_for_posts')}")
