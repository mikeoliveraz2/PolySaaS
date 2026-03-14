"""
Build the Blog listing page with all published posts.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get all posts with excerpts
r = s.get(f"{AZURE}/wp-json/wp/v2/posts", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,title,excerpt,date,content"
})
posts = r.json()
posts.sort(key=lambda p: p['date'], reverse=True)

print(f"Found {len(posts)} posts")

# Get the blog page
r2 = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
})
pages = {p['slug']: p for p in r2.json()}
blog_page = pages['blog']

raw = blog_page['content']['raw']

# Extract existing CSS and toggle blocks
blocks = re.findall(r'(<!-- wp:html -->.*?<!-- /wp:html -->)', raw, re.DOTALL)
preserved = []
for block in blocks:
    if '<style>' in block or 'ps-theme-toggle' in block:
        preserved.append(block)

# Build blog listing
post_cards = ""
for post in posts:
    title = post['title']['raw'] if isinstance(post['title'], dict) else post['title']
    
    # Get excerpt - strip HTML, clean up
    excerpt_raw = post['excerpt']['raw'] if isinstance(post['excerpt'], dict) else post['excerpt']
    if not excerpt_raw:
        # Generate excerpt from content
        content = post['content']['raw'] if isinstance(post['content'], dict) else post['content']
        text = re.sub(r'<[^>]+>', ' ', content)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)  # strip CSS comments
        text = re.sub(r'\{[^}]+\}', '', text)  # strip CSS rules
        text = re.sub(r'\s+', ' ', text).strip()
        # Skip CSS-only content
        if text.startswith(':root') or text.startswith('/*'):
            text = ""
        excerpt = text[:250] + '...' if len(text) > 250 else text
    else:
        excerpt = re.sub(r'<[^>]+>', '', excerpt_raw).strip()
        excerpt = excerpt[:250] + '...' if len(excerpt) > 250 else excerpt
    
    # Format date
    date_str = post['date'][:10]
    from datetime import datetime
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = dt.strftime('%B %d, %Y')
    except:
        formatted_date = date_str
    
    post_url = f"{AZURE}/{post['slug']}/"
    
    post_cards += f'''
<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:24px;margin-bottom:20px;transition:box-shadow 0.2s ease;">
<span style="color:var(--ps-text-muted,#6B7280);font-size:0.85rem;">{formatted_date}</span>
<h3 style="color:var(--ps-primary,#001F3F);margin:8px 0 10px;font-size:1.25rem;"><a href="{post_url}" style="text-decoration:none;color:inherit;">{title}</a></h3>
<p style="color:var(--ps-text,#1F2937);margin:0 0 12px;line-height:1.6;font-size:0.95rem;">{excerpt}</p>
<a href="{post_url}" style="color:var(--ps-accent,#0F766E);font-weight:600;text-decoration:none;font-size:0.9rem;">Read More &rarr;</a>
</div>'''

content_block = f'''<!-- wp:html -->
<h2 style="text-align:center;padding:10px 0;margin:0;color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;">Blog</h2>
<p style="text-align:center;color:var(--ps-text-muted,#6B7280);font-size:1.05rem;margin:0 0 32px;">News, insights, and updates from the PolySaaS team.</p>

<div style="max-width:800px;margin:0 auto;padding:0 20px;">
{post_cards}
</div>
<!-- /wp:html -->'''

# Also check if dark mode CSS is present
has_dark_mode = '--ps-primary: #60A5FA' in raw
if not has_dark_mode:
    # Get dark mode CSS from homepage
    home_raw = pages['home']['content']['raw']
    all_styles = re.findall(r'<style>(.*?)</style>', home_raw, re.DOTALL)
    dm_parts = []
    for st in all_styles:
        if 'body.dark-mode' in st or '--ps-primary: #60A5FA' in st:
            clean = re.sub(r'</?p>', '', st).strip()
            dm_parts.append(clean)
    if dm_parts:
        dm_css = '\n\n'.join(dm_parts)
        dm_block = f'<!-- wp:html -->\n<style>\n{dm_css}\n</style>\n<!-- /wp:html -->'
        preserved.append(dm_block)
        print("Added dark mode CSS")

new_content = '\n'.join(preserved) + '\n' + content_block

r3 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{blog_page['id']}", json={"content": new_content})
if r3.status_code == 200:
    print("SUCCESS: Blog page updated with post listings")
else:
    print(f"FAILED: {r3.status_code}")
    print(r3.text[:500])
