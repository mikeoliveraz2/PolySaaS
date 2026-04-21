"""
Properly extract and inject dark mode CSS to all inner pages.
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

# Get homepage content
home_raw = page_map['home']['content']['raw']

# Find all <!-- wp:html --> blocks
home_blocks = re.findall(r'(<!-- wp:html -->.*?<!-- /wp:html -->)', home_raw, re.DOTALL)
print(f"Homepage has {len(home_blocks)} wp:html blocks")

for i, b in enumerate(home_blocks):
    has_dm = 'body.dark-mode' in b
    has_toggle = 'ps-theme-toggle' in b
    has_root = ':root' in b
    print(f"  Block {i}: dark-mode={has_dm}, toggle={has_toggle}, :root={has_root}, len={len(b)}")

# The dark mode CSS blocks are those with body.dark-mode OR :root CSS vars
darkmode_css_blocks = []
for b in home_blocks:
    if ('body.dark-mode' in b or ':root' in b) and 'ps-theme-toggle' not in b:
        darkmode_css_blocks.append(b)
    elif 'body.dark-mode' in b and 'ps-theme-toggle' in b:
        # This is the combined toggle+CSS block, extract just the style parts
        style_parts = re.findall(r'<style>(.*?)</style>', b, re.DOTALL)
        for sp in style_parts:
            if 'body.dark-mode' in sp or ':root' in sp:
                darkmode_css_blocks.append(f'<!-- wp:html -->\n<style>\n{sp}\n</style>\n<!-- /wp:html -->')

print(f"\nExtracted {len(darkmode_css_blocks)} dark mode CSS blocks")

if not darkmode_css_blocks:
    # Fallback: extract ALL style blocks from homepage that contain dark mode rules
    all_styles = re.findall(r'<style>(.*?)</style>', home_raw, re.DOTALL)
    for st in all_styles:
        if 'body.dark-mode' in st or '--ps-primary: #60A5FA' in st:
            darkmode_css_blocks.append(f'<!-- wp:html -->\n<style>\n{st}\n</style>\n<!-- /wp:html -->')
            print(f"  Fallback extracted style block ({len(st)} chars)")
    
    print(f"After fallback: {len(darkmode_css_blocks)} dark mode CSS blocks")

if not darkmode_css_blocks:
    print("ERROR: Could not find dark mode CSS on homepage!")
    sys.exit(1)

# Target pages
TARGET_SLUGS = [
    'odoo', 'nextcloud', 'mattermost', 'wordpress-3', 'liferay-2',
    'dolibarr-3', 'monitor-logger-4', 'polysysmon',
    'architecture', 'portal', 'dynamic-orchestration', 'polysniffer',
    'apps-as-peers', 'openapi-2', 'ai-as-peers', 'bundled-applications'
]

dm_css_combined = '\n'.join(darkmode_css_blocks)

fixed = 0
for slug in TARGET_SLUGS:
    if slug not in page_map:
        print(f"  {slug}: NOT FOUND")
        continue
    
    page = page_map[slug]
    raw = page['content']['raw']
    
    # Check if this page already has the full dark mode system
    if '--ps-primary: #60A5FA' in raw:
        print(f"  {slug}: already has full dark mode CSS, skipping")
        continue
    
    # Insert dark mode blocks after the toggle block
    toggle_match = re.search(r'(<!-- wp:html -->.*?ps-theme-toggle.*?<!-- /wp:html -->)', raw, re.DOTALL)
    if toggle_match:
        insert_pos = toggle_match.end()
        new_raw = raw[:insert_pos] + '\n' + dm_css_combined + raw[insert_pos:]
    else:
        first_block_end = re.search(r'<!-- /wp:html -->', raw)
        if first_block_end:
            insert_pos = first_block_end.end()
            new_raw = raw[:insert_pos] + '\n' + dm_css_combined + raw[insert_pos:]
        else:
            new_raw = dm_css_combined + '\n' + raw
    
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page['id']}", json={"content": new_raw})
    if r2.status_code == 200:
        fixed += 1
        print(f"  {slug}: dark mode CSS injected")
    else:
        print(f"  {slug}: FAILED {r2.status_code}")

print(f"\nFixed {fixed} pages")
