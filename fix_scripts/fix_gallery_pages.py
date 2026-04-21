"""
Fix Gallery Images and Gallery Videos pages with proper content.
Also fix the oversized logo issue on these pages.
"""
import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get all pages
r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content,title"
})
pages = {p['slug']: p for p in r.json()}

# Check current content of gallery pages
for slug in ['gallery-images', 'gallery-videos']:
    p = pages.get(slug)
    if p:
        raw = p['content']['raw']
        print(f"{slug} (id={p['id']}): {len(raw)} chars raw")
        has_logo_css = 'Header Logo Size Override' in raw
        has_toggle = 'ps-theme-toggle' in raw
        has_darkmode = '--ps-primary: #60A5FA' in raw
        print(f"  Logo CSS: {has_logo_css}, Toggle: {has_toggle}, Dark mode: {has_darkmode}")

# Get media library images to display in gallery
r2 = s.get(f"{AZURE}/wp-json/wp/v2/media", params={
    "per_page": 100, "media_type": "image", "_fields": "id,source_url,alt_text,title,caption"
})
media = r2.json()
print(f"\nFound {len(media)} images in media library")
for m in media[:30]:
    title = m['title']['rendered'] if isinstance(m['title'], dict) else m['title']
    alt = m.get('alt_text', '')
    url = m['source_url']
    print(f"  {title}: {url}")

# Get homepage for CSS/toggle/dark mode blocks to reuse
home = pages['home']
home_raw = home['content']['raw']

# Extract logo CSS block
logo_css_match = re.search(r'(<!-- wp:html -->\s*<style>\s*/\* PolySaaS Header Logo.*?<!-- /wp:html -->)', home_raw, re.DOTALL)
logo_css_block = logo_css_match.group(1) if logo_css_match else ''

# Extract toggle block
toggle_match = re.search(r'(<!-- wp:html -->\s*<button class="ps-theme-toggle".*?<!-- /wp:html -->)', home_raw, re.DOTALL)
toggle_block = toggle_match.group(1) if toggle_match else ''

# Extract clean dark mode CSS (from inner pages that have it clean)
arch = pages.get('architecture')
if arch:
    arch_raw = arch['content']['raw']
    dm_match = re.search(r'(<!-- wp:html -->\s*<style>\s*/\* Dark mode nav.*?<!-- /wp:html -->)', arch_raw, re.DOTALL)
    dm_block = dm_match.group(1) if dm_match else ''
    
    # Also get the full dark mode system CSS
    full_dm_match = re.search(r'(<!-- wp:html -->\s*<style>\s*/\* ===== POLYSAAS DARK/LIGHT MODE SYSTEM.*?<!-- /wp:html -->)', arch_raw, re.DOTALL)
    full_dm_block = full_dm_match.group(1) if full_dm_match else ''
else:
    dm_block = ''
    full_dm_block = ''

print(f"\nLogo CSS: {len(logo_css_block)} chars")
print(f"Toggle: {len(toggle_block)} chars")
print(f"Dark mode nav: {len(dm_block)} chars")
print(f"Dark mode full: {len(full_dm_block)} chars")

# Filter gallery-worthy images (skip tiny icons, favicons, etc.)
gallery_images = []
skip_patterns = ['favicon', 'cropped-', 'logo', '150x150', '300x300']
for m in media:
    url = m['source_url']
    title = m['title']['rendered'] if isinstance(m['title'], dict) else m['title']
    alt = m.get('alt_text', '') or title
    
    # Skip small/utility images
    if any(s in url.lower() for s in skip_patterns):
        continue
    gallery_images.append((url, alt, title))

print(f"\n{len(gallery_images)} gallery-worthy images")

# Build Gallery Images page
image_grid = ""
for url, alt, title in gallery_images:
    image_grid += f'''
<div style="break-inside:avoid;margin-bottom:16px;">
<img src="{url}" alt="{alt}" style="width:100%;border-radius:8px;display:block;box-shadow:0 2px 8px rgba(0,0,0,0.1);" loading="lazy" />
<p style="color:var(--ps-text-muted,#6B7280);font-size:0.8rem;margin:6px 0 0;text-align:center;">{alt}</p>
</div>'''

images_content = f'''<!-- wp:html -->
<h2 style="text-align:center;padding:10px 0;margin:0;color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;">Image Gallery</h2>
<p style="text-align:center;color:var(--ps-text-muted,#6B7280);font-size:1.05rem;margin:0 0 32px;">Screenshots, diagrams, and visuals from the PolySaaS platform.</p>

<div style="max-width:900px;margin:0 auto;padding:0 20px;columns:2;column-gap:16px;">
{image_grid}
</div>
<!-- /wp:html -->'''

# Build Gallery Videos page  
videos_content = f'''<!-- wp:html -->
<h2 style="text-align:center;padding:10px 0;margin:0;color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;">Video Gallery</h2>
<p style="text-align:center;color:var(--ps-text-muted,#6B7280);font-size:1.05rem;margin:0 0 32px;">Demos, walkthroughs, and presentations from the PolySaaS team.</p>

<div style="max-width:800px;margin:0 auto;padding:0 20px;">

<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:40px;text-align:center;">
<p style="font-size:3rem;margin:0 0 16px;">🎬</p>
<h3 style="color:var(--ps-primary,#001F3F);margin:0 0 8px;font-size:1.3rem;">Coming Soon</h3>
<p style="color:var(--ps-text-muted,#6B7280);margin:0;line-height:1.6;">Platform demo videos, feature walkthroughs, and customer testimonials are in production. Check back soon for updates.</p>
</div>

</div>
<!-- /wp:html -->'''

# Assemble full page content for each
base_blocks = '\n'.join(filter(None, [logo_css_block, toggle_block, dm_block, full_dm_block]))

for slug, content_block, label in [
    ('gallery-images', images_content, 'Gallery Images'),
    ('gallery-videos', videos_content, 'Gallery Videos'),
]:
    page = pages[slug]
    new_content = base_blocks + '\n' + content_block
    
    r3 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page['id']}", json={"content": new_content})
    if r3.status_code == 200:
        print(f"  {label}: updated successfully")
    else:
        print(f"  {label}: FAILED {r3.status_code}")
