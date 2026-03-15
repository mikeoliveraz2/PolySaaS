"""
Standardize page titles across all pages to match homepage style.

Homepage has:
  <h2 style="text-align:center;padding:5px 0 0 0;margin:0;
      color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;">
      Industrial Strength SaaS for Limitless Horizons</h2>

This script adds the same styled H2 title to every inner page,
inserted right after the dark mode toggle block.
"""
import requests, re

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

TITLE_STYLE = 'style="text-align:center;padding:5px 0 0 0;margin:0;color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;"'

def make_title_block(title):
    return f'\n<!-- wp:html -->\n<h2 {TITLE_STYLE}>{title}</h2>\n<!-- /wp:html -->'

def find_insertion_point(content):
    """Find where to insert the title: right after the toggle button's <!-- /wp:html -->"""
    toggle_idx = content.find('ps-dark-toggle')
    if toggle_idx >= 0:
        # Find the closing </button> or </script> after toggle
        # Then find the next <!-- /wp:html -->
        wp_close = content.find('<!-- /wp:html -->', toggle_idx)
        if wp_close >= 0:
            return wp_close + len('<!-- /wp:html -->')
    
    # Fallback: after the first <!-- /wp:html --> (end of first style block)
    first_close = content.find('<!-- /wp:html -->')
    if first_close >= 0:
        return first_close + len('<!-- /wp:html -->')
    
    # Last resort: beginning of content
    return 0

def already_has_title(content, page_title):
    """Check if the page already has a title H2 in the homepage style"""
    pattern = rf'<h2\s[^>]*>{re.escape(page_title)}</h2>'
    match = re.search(pattern, content)
    if match:
        # Check it's in the right style (not inside a wp-block-group grey band)
        ctx_start = max(0, match.start() - 100)
        context = content[ctx_start:match.start()]
        if 'wp-block-group' not in context:
            return True
    return False

# Get all published pages
r = s.get(f"{AZURE}/wp-json/wp/v2/pages?per_page=100&status=publish&context=edit")
pages = r.json()
print(f"Found {len(pages)} published pages\n")

skip_slugs = ['home']  # Homepage already has its title
updated = 0
skipped = 0

for page in sorted(pages, key=lambda x: x['title']['raw']):
    pid = page['id']
    title = page['title']['raw']
    slug = page['slug']
    content = page['content']['raw']
    
    if slug in skip_slugs:
        print(f"  SKIP [{pid}] {title} (homepage)")
        skipped += 1
        continue
    
    if not title.strip():
        print(f"  SKIP [{pid}] (no title, slug={slug})")
        skipped += 1
        continue
    
    # Check if already has the title in homepage style
    if already_has_title(content, title):
        print(f"  OK   [{pid}] {title} - already has styled title")
        skipped += 1
        continue
    
    # Remove any old-style title that's in a grey-band wp-block-group
    # Pattern: <p><!-- Hero Section --></p> <div class="wp-block-group"...> ... <h2>Title</h2> ... </div></div>
    old_hero = re.search(
        r'<p>\s*<!--\s*Hero Section\s*-->\s*</p>\s*'
        r'<div class="wp-block-group"[^>]*>\s*'
        r'<div class="wp-block-group__inner-container">\s*'
        r'<h2[^>]*>[^<]*</h2>\s*',
        content
    )
    if old_hero:
        content = content[:old_hero.start()] + content[old_hero.end():]
        print(f"  CLEAN [{pid}] {title} - removed old hero-style title")
    
    # Find insertion point
    insert_at = find_insertion_point(content)
    
    # Insert the title
    title_block = make_title_block(title)
    new_content = content[:insert_at] + title_block + content[insert_at:]
    
    # Update via API
    r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}",
        json={"content": new_content})
    
    if r.status_code == 200:
        print(f"  DONE [{pid}] {title}")
        updated += 1
    else:
        print(f"  FAIL [{pid}] {title} - {r.status_code}: {r.text[:200]}")

print(f"\nSummary: {updated} updated, {skipped} skipped")
