"""Build the blog archive page with pre-rendered post cards (no JS needed).
   Fixes HTML entity encoding and hides Bricks default title."""
import requests
import re
from html import unescape
from datetime import datetime

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

session = requests.Session()
session.auth = (USER, APP_PASS)

r = session.get(f"{SITE}/wp-json/wp/v2/posts", params={
    "per_page": 50,
    "status": "publish",
    "_embed": "true",
    "orderby": "date",
    "order": "desc"
})
posts = r.json()
print(f"Fetched {len(posts)} published posts")

def format_date(iso_str):
    dt = datetime.fromisoformat(iso_str)
    return dt.strftime("%B %d, %Y")

def strip_html(html_str):
    clean = re.sub(r'<[^>]+>', '', html_str)
    clean = unescape(clean)
    clean = re.sub(r'\*\*(.+?)\*\*', r'\1', clean)
    clean = re.sub(r'\*(.+?)\*', r'\1', clean)
    return clean.strip()

def truncate(s, length=160):
    if len(s) <= length:
        return s
    return s[:length].rsplit(' ', 1)[0] + '...'

def safe_attr(text):
    """Escape for HTML attributes only."""
    return text.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')

cards_html = ""
for post in posts:
    title = unescape(post['title']['rendered'])
    link = post['link']
    date = format_date(post['date'])
    excerpt = truncate(strip_html(post['excerpt']['rendered']))

    featured_img = ""
    if post.get('_embedded') and post['_embedded'].get('wp:featuredmedia'):
        media = post['_embedded']['wp:featuredmedia']
        if media and len(media) > 0 and media[0].get('source_url'):
            featured_img = media[0]['source_url']

    if featured_img:
        img_html = f'<div class="blog-card__image"><a href="{link}"><img src="{safe_attr(featured_img)}" alt="{safe_attr(title)}" loading="lazy"></a></div>'
    else:
        img_html = f'<div class="blog-card__image blog-card__image--placeholder"><a href="{link}"><div class="blog-card__image-fallback"><span>PolySaaS</span></div></a></div>'

    cards_html += f'''    <article class="blog-card">
      {img_html}
      <div class="blog-card__body">
        <time class="blog-card__date">{date}</time>
        <h2 class="blog-card__title"><a href="{link}">{title}</a></h2>
        <p class="blog-card__excerpt">{excerpt}</p>
        <a href="{link}" class="blog-card__read-more">Read Article &rarr;</a>
      </div>
    </article>
'''

page_html = f'''<!-- wp:html -->
<div class="polysaas-blog-archive">
  <div class="blog-hero">
    <h1 class="blog-hero__title">PolySaaS Blog</h1>
    <p class="blog-hero__subtitle">Insights on SaaS orchestration, AI collaboration, and building the future of enterprise software.</p>
  </div>

  <div class="blog-grid">
{cards_html}  </div>
</div>
<!-- /wp:html -->'''

print("Updating blog page (ID 1347)...")
r_up = session.post(f"{SITE}/wp-json/wp/v2/pages/1347", json={
    "content": page_html,
    "status": "publish"
})

if r_up.status_code == 200:
    print("Blog page updated successfully")
else:
    print(f"Update failed: {r_up.status_code}")
    print(r_up.text[:300])

print("Done!")
