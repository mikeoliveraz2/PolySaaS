"""Audit current blog posts and template structure on the WordPress site."""
import requests
import re
import json

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

session = requests.Session()
session.auth = (USER, APP_PASS)

# 1. Get all blog posts
print("=== BLOG POSTS ===")
r = session.get(f"{SITE}/wp-json/wp/v2/posts", params={"per_page": 20, "status": "publish,draft"})
if r.status_code == 200:
    posts = r.json()
    print(f"  Total posts: {len(posts)}")
    for p in posts:
        print(f"  ID={p['id']}  status={p['status']}  title='{p['title']['rendered']}'")
        print(f"    slug=/{p['slug']}/  date={p['date']}")
        cats = p.get('categories', [])
        tags = p.get('tags', [])
        featured = p.get('featured_media', 0)
        print(f"    categories={cats}  tags={tags}  featured_media={featured}")
else:
    print(f"  Posts API: {r.status_code}")

# 2. Get categories
print("\n=== CATEGORIES ===")
r = session.get(f"{SITE}/wp-json/wp/v2/categories", params={"per_page": 50})
if r.status_code == 200:
    for cat in r.json():
        print(f"  ID={cat['id']}  name='{cat['name']}'  slug='{cat['slug']}'  count={cat['count']}")

# 3. Get tags
print("\n=== TAGS ===")
r = session.get(f"{SITE}/wp-json/wp/v2/tags", params={"per_page": 50})
if r.status_code == 200:
    tags = r.json()
    if tags:
        for t in tags:
            print(f"  ID={t['id']}  name='{t['name']}'  count={t['count']}")
    else:
        print("  No tags found")

# 4. Check current single post rendered HTML structure
print("\n=== SINGLE POST STRUCTURE (first published post) ===")
r = session.get(f"{SITE}/wp-json/wp/v2/posts", params={"per_page": 1, "status": "publish"})
if r.status_code == 200 and r.json():
    post = r.json()[0]
    post_url = post['link']
    print(f"  Checking: {post_url}")
    rp = requests.get(post_url, timeout=20)
    html = rp.text

    # Check if Bricks renders this or default WP
    if 'brxe-' in html:
        print("  Rendered by: BRICKS BUILDER")
    elif 'entry-content' in html:
        print("  Rendered by: DEFAULT WORDPRESS THEME")
    else:
        print("  Rendered by: UNKNOWN")

    # Check for blog-specific elements
    for pattern_name, pattern in [
        ("Post title", r'<h[12][^>]*class="[^"]*(?:entry-title|post-title|brxe-post-title)[^"]*"'),
        ("Post date", r'(?:entry-date|post-date|brxe-post-date|published)'),
        ("Post author", r'(?:entry-author|post-author|brxe-post-author|author-name)'),
        ("Post content", r'(?:entry-content|post-content|brxe-post-content)'),
        ("Featured image", r'(?:post-thumbnail|featured-image|wp-post-image)'),
        ("Comments", r'(?:comments-area|comment-list|respond)'),
        ("Sidebar", r'(?:sidebar|widget-area)'),
        ("Breadcrumbs", r'(?:breadcrumb|brxe-breadcrumbs)'),
    ]:
        found = bool(re.search(pattern, html, re.IGNORECASE))
        print(f"  {pattern_name}: {'YES' if found else 'NO'}")

# 5. Check existing Bricks templates
print("\n=== BRICKS TEMPLATES (via REST API) ===")
for endpoint in ["bricks_template", "bricks-template", "bricks_templates"]:
    r = session.get(f"{SITE}/wp-json/wp/v2/{endpoint}", params={"per_page": 50})
    print(f"  /wp/v2/{endpoint}: {r.status_code}")
    if r.status_code == 200:
        for t in r.json():
            print(f"    ID={t['id']}  title='{t.get('title',{}).get('rendered','')}'  status={t.get('status','')}")

# 6. Check blog page / archive page
print("\n=== BLOG/ARCHIVE PAGE ===")
r = session.get(f"{SITE}/wp-json/wp/v2/settings")
if r.status_code == 200:
    settings = r.json()
    print(f"  posts_per_page: {settings.get('posts_per_page')}")
    print(f"  page_for_posts: {settings.get('page_for_posts')}")
    print(f"  page_on_front: {settings.get('page_on_front')}")
    print(f"  show_on_front: {settings.get('show_on_front')}")

# 7. Fetch a single post page and extract the full body structure
print("\n=== SINGLE POST BODY CLASSES ===")
if r.status_code == 200 and posts:
    post_url = posts[0]['link']
    rp = requests.get(post_url, timeout=20)
    body_match = re.search(r'<body[^>]*class="([^"]*)"', rp.text)
    if body_match:
        print(f"  Body classes: {body_match.group(1)}")

print("\n=== DONE ===")
