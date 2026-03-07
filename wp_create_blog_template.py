"""Create a styled blog archive page and generate blog template CSS."""
import requests
import json

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

session = requests.Session()
session.auth = (USER, APP_PASS)

# Blog archive page content with dynamic post loading
BLOG_PAGE_HTML = """<!-- wp:html -->
<div class="polysaas-blog-archive">
  <div class="blog-hero">
    <h1 class="blog-hero__title">PolySaaS Blog</h1>
    <p class="blog-hero__subtitle">Insights on SaaS orchestration, AI collaboration, and building the future of enterprise software.</p>
  </div>

  <div class="blog-grid" id="polysaas-blog-grid">
    <p class="blog-loading">Loading posts...</p>
  </div>

  <div class="blog-load-more" id="blog-load-more" style="display:none;">
    <button class="blog-load-more__btn" id="blog-load-more-btn">Load More</button>
  </div>
</div>

<script>
(function() {
  const grid = document.getElementById('polysaas-blog-grid');
  const loadMoreWrap = document.getElementById('blog-load-more');
  const loadMoreBtn = document.getElementById('blog-load-more-btn');
  let page = 1;
  const perPage = 6;
  let totalPages = 1;

  function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  }

  function stripHtml(html) {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
  }

  function truncate(str, len) {
    if (str.length <= len) return str;
    return str.substring(0, len).trim() + '...';
  }

  function createCard(post) {
    const excerpt = truncate(stripHtml(post.excerpt.rendered), 160);
    const date = formatDate(post.date);
    const title = post.title.rendered;
    const link = post.link;
    const featuredImg = post._embedded && post._embedded['wp:featuredmedia'] && post._embedded['wp:featuredmedia'][0]
      ? post._embedded['wp:featuredmedia'][0].source_url
      : '';

    const card = document.createElement('article');
    card.className = 'blog-card';
    card.innerHTML =
      (featuredImg
        ? '<div class="blog-card__image"><a href="' + link + '"><img src="' + featuredImg + '" alt="' + title + '" loading="lazy"></a></div>'
        : '<div class="blog-card__image blog-card__image--placeholder"><a href="' + link + '"><div class="blog-card__image-fallback"><span>PolySaaS</span></div></a></div>') +
      '<div class="blog-card__body">' +
        '<time class="blog-card__date">' + date + '</time>' +
        '<h2 class="blog-card__title"><a href="' + link + '">' + title + '</a></h2>' +
        '<p class="blog-card__excerpt">' + excerpt + '</p>' +
        '<a href="' + link + '" class="blog-card__read-more">Read Article &rarr;</a>' +
      '</div>';
    return card;
  }

  function loadPosts() {
    const url = '/wp-json/wp/v2/posts?per_page=' + perPage + '&page=' + page + '&_embed';
    fetch(url)
      .then(function(resp) {
        totalPages = parseInt(resp.headers.get('X-WP-TotalPages') || '1');
        return resp.json();
      })
      .then(function(posts) {
        if (page === 1) grid.innerHTML = '';

        posts.forEach(function(post) {
          grid.appendChild(createCard(post));
        });

        if (page < totalPages) {
          loadMoreWrap.style.display = 'flex';
        } else {
          loadMoreWrap.style.display = 'none';
        }
        page++;
      })
      .catch(function(err) {
        if (page === 1) grid.innerHTML = '<p class="blog-error">Unable to load posts. Please try again later.</p>';
      });
  }

  loadMoreBtn.addEventListener('click', loadPosts);
  loadPosts();
})();
</script>
<!-- /wp:html -->"""

# Step 1: Update the existing /blog/ page (ID 1347) or create if needed
print("=== Step 1: Update Blog Archive Page ===")
r = session.get(f"{SITE}/wp-json/wp/v2/pages/1347", params={"context": "edit"})
if r.status_code == 200:
    page = r.json()
    print(f"  Found existing blog page: ID={page['id']} title='{page['title']['raw']}'")
    # Update with our content
    r_up = session.post(f"{SITE}/wp-json/wp/v2/pages/1347", json={
        "content": BLOG_PAGE_HTML,
        "status": "publish"
    })
    if r_up.status_code == 200:
        print(f"  Blog page updated successfully")
    else:
        print(f"  Update failed: {r_up.status_code} - {r_up.text[:200]}")
else:
    print(f"  Page 1347 not found ({r.status_code}), creating new blog page...")
    r_new = session.post(f"{SITE}/wp-json/wp/v2/pages", json={
        "title": "Blog",
        "slug": "blog",
        "content": BLOG_PAGE_HTML,
        "status": "publish"
    })
    if r_new.status_code in (200, 201):
        print(f"  Created blog page: ID={r_new.json()['id']}")
    else:
        print(f"  Create failed: {r_new.status_code} - {r_new.text[:200]}")

# Step 2: Make sure "Hello world!" post is deleted or drafted
print("\n=== Step 2: Clean up Hello World post ===")
r = session.get(f"{SITE}/wp-json/wp/v2/posts/1", params={"context": "edit"})
if r.status_code == 200:
    post = r.json()
    if post['status'] == 'publish':
        r_up = session.post(f"{SITE}/wp-json/wp/v2/posts/1", json={"status": "draft"})
        if r_up.status_code == 200:
            print("  'Hello world!' post moved to draft")
        else:
            print(f"  Failed to draft: {r_up.status_code}")
    else:
        print(f"  Already {post['status']}")

print("\n=== DONE ===")
