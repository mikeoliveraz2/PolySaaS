"""
Inject the dark mode CSS from homepage into all inner pages that are missing it.
The homepage has 3 CSS blocks: logo, dark-mode-nav, and the full dark mode system.
Inner pages only have the logo CSS. We need to copy the other two.
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

# Get dark mode CSS blocks from homepage
home_raw = page_map['home']['content']['raw']
home_html_blocks = re.findall(r'(<!-- wp:html -->.*?<!-- /wp:html -->)', home_raw, re.DOTALL)

# Identify the dark mode CSS blocks (the ones with body.dark-mode that aren't the toggle)
darkmode_blocks = []
for block in home_html_blocks:
    if 'body.dark-mode' in block and 'ps-theme-toggle' not in block:
        darkmode_blocks.append(block)

print(f"Found {len(darkmode_blocks)} dark mode CSS blocks on homepage")

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
        print(f"  {slug}: NOT FOUND")
        continue
    
    page = page_map[slug]
    raw = page['content']['raw']
    
    if 'body.dark-mode' in raw and ':root' in raw and '--ps-primary: #60A5FA' in raw:
        print(f"  {slug}: already has dark mode CSS, skipping")
        continue
    
    # Insert dark mode blocks right after the toggle block
    # Find the toggle block end position
    toggle_match = re.search(r'(<!-- wp:html -->.*?ps-theme-toggle.*?<!-- /wp:html -->)', raw, re.DOTALL)
    if toggle_match:
        insert_pos = toggle_match.end()
        new_raw = raw[:insert_pos] + '\n' + '\n'.join(darkmode_blocks) + raw[insert_pos:]
    else:
        # No toggle found, insert after the first wp:html block (logo CSS)
        first_block = re.search(r'<!-- /wp:html -->', raw)
        if first_block:
            insert_pos = first_block.end()
            new_raw = raw[:insert_pos] + '\n' + '\n'.join(darkmode_blocks) + raw[insert_pos:]
        else:
            new_raw = '\n'.join(darkmode_blocks) + '\n' + raw
    
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page['id']}", json={"content": new_raw})
    if r2.status_code == 200:
        fixed += 1
        print(f"  {slug}: dark mode CSS injected")
    else:
        print(f"  {slug}: FAILED {r2.status_code}")

print(f"\nFixed {fixed} pages")
