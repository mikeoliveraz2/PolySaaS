"""
Clean and inject proper dark mode CSS into all inner pages.
Extracts CSS from homepage, strips wpautop corruption, and injects clean CSS.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
})
all_pages = r.json()
page_map = {p['slug']: p for p in all_pages}

# Extract dark mode CSS from homepage and clean it
home_raw = page_map['home']['content']['raw']
style_blocks = re.findall(r'<style>(.*?)</style>', home_raw, re.DOTALL)

clean_dm_css_parts = []
for sb in style_blocks:
    if 'body.dark-mode' in sb or ':root' in sb:
        # Strip all HTML tags that wpautop injected
        clean = re.sub(r'</?p>', '', sb)
        clean = re.sub(r'<br\s*/?>', '', clean)
        clean = clean.strip()
        clean_dm_css_parts.append(clean)

if not clean_dm_css_parts:
    print("ERROR: No dark mode CSS found on homepage")
    sys.exit(1)

# Combine into one clean CSS block
CLEAN_DARK_MODE_CSS = '\n\n'.join(clean_dm_css_parts)
CLEAN_CSS_BLOCK = f'<!-- wp:html -->\n<style>\n{CLEAN_DARK_MODE_CSS}\n</style>\n<!-- /wp:html -->'

print(f"Clean dark mode CSS: {len(CLEAN_DARK_MODE_CSS)} chars")
# Verify it's valid (no <p> tags)
assert '<p>' not in CLEAN_DARK_MODE_CSS, "CSS still has <p> tags!"
assert '</p>' not in CLEAN_DARK_MODE_CSS, "CSS still has </p> tags!"
print("Verified: no HTML contamination in CSS")

# Target pages
TARGET_SLUGS = [
    'odoo', 'nextcloud', 'mattermost', 'wordpress-3', 'liferay-2',
    'dolibarr-3', 'monitor-logger-4', 'polysysmon',
    'architecture', 'portal', 'dynamic-orchestration', 'polysniffer',
    'apps-as-peers', 'openapi-2', 'ai-as-peers', 'bundled-applications'
]

fixed = 0
for slug in TARGET_SLUGS:
    if slug not in page_map:
        continue
    
    page = page_map[slug]
    raw = page['content']['raw']
    
    # Remove any existing corrupted dark mode CSS blocks
    # Keep: logo CSS block, toggle block, and content block
    # Remove: any style block with body.dark-mode or :root { --ps-primary
    
    blocks = re.findall(r'(<!-- wp:html -->.*?<!-- /wp:html -->)', raw, re.DOTALL)
    
    kept_blocks = []
    for block in blocks:
        # Keep blocks that are: toggle, logo CSS, or content
        if 'ps-theme-toggle' in block:
            kept_blocks.append(block)
        elif 'body.dark-mode' in block or '--ps-primary: #60A5FA' in block or 'POLYSAAS DARK/LIGHT MODE SYSTEM' in block:
            # Skip dark mode CSS blocks - we'll add clean one
            continue
        elif 'Dark mode nav visibility' in block:
            # Skip the nav dark mode CSS too
            continue
        else:
            kept_blocks.append(block)
    
    # Rebuild: logo block + toggle + clean dark mode CSS + content
    # Find which blocks are which
    logo_blocks = [b for b in kept_blocks if 'Header Logo Size Override' in b]
    toggle_blocks = [b for b in kept_blocks if 'ps-theme-toggle' in b]
    content_blocks = [b for b in kept_blocks if b not in logo_blocks and b not in toggle_blocks]
    
    new_raw = '\n'.join(logo_blocks + toggle_blocks + [CLEAN_CSS_BLOCK] + content_blocks)
    
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page['id']}", json={"content": new_raw})
    if r2.status_code == 200:
        fixed += 1
        print(f"  {slug}: clean dark mode CSS applied")
    else:
        print(f"  {slug}: FAILED {r2.status_code}")

print(f"\nFixed {fixed}/{len(TARGET_SLUGS)} pages")
