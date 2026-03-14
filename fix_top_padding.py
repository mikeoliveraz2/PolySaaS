"""
Reduce whitespace/padding at the top of ALL pages:
- Reduce .content-area top margin (Kadence default is 5rem)
- Reduce .entry-content-wrap top padding
- Reduce entry-hero padding
- Apply to all pages, not just homepage
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from wp_snapshot import take_snapshot
take_snapshot("before reducing top padding on all pages")

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

PADDING_CSS = """/* Reduce top whitespace on all pages */
.content-area { margin-top: 1rem !important; margin-bottom: 2rem !important; }
.entry-content-wrap { padding-top: 0.5rem !important; }
.entry-hero-container-inner { padding-top: 0 !important; padding-bottom: 0 !important; min-height: 0 !important; }
.entry-hero .entry-header { min-height: 0 !important; padding: 10px 0 !important; }
h1.entry-title, .entry-hero h1 { margin-top: 0 !important; margin-bottom: 8px !important; padding-top: 0 !important; }
.content-bg { padding-top: 0 !important; }
"""

r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
})
pages = r.json()
print(f"Found {len(pages)} pages")

fixed = 0
for page in pages:
    pid = page['id']
    slug = page['slug']
    raw = page['content']['raw']
    
    if not raw.strip():
        continue
    
    if 'Reduce top whitespace on all pages' in raw:
        continue
    
    # Find the header logo CSS block and append our padding CSS to it
    logo_css = re.search(
        r'(<!-- wp:html -->\s*<style>\s*/\* PolySaaS Header Logo Size Override \*/.*?)(</style>\s*<!-- /wp:html -->)',
        raw, re.DOTALL
    )
    
    if logo_css:
        # Remove any old homepage-only padding CSS
        old_home_css = '/* Reduce homepage top padding */\n.home .content-area { margin-top: 1rem !important; }\n.home .entry-content-wrap { padding-top: 0.5rem !important; }\n'
        raw = raw.replace(old_home_css, '')
        
        # Re-find after removal
        logo_css = re.search(
            r'(<!-- wp:html -->\s*<style>\s*/\* PolySaaS Header Logo Size Override \*/.*?)(</style>\s*<!-- /wp:html -->)',
            raw, re.DOTALL
        )
        
        if logo_css:
            raw = raw.replace(logo_css.group(0),
                logo_css.group(1) + '\n' + PADDING_CSS + logo_css.group(2))
    else:
        # No logo CSS block - create a new style block at the top
        css_block = f'<!-- wp:html -->\n<style>\n{PADDING_CSS}\n</style>\n<!-- /wp:html -->\n'
        raw = css_block + raw
    
    r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": raw})
    if r2.status_code == 200:
        fixed += 1
        print(f"  {slug}: padding reduced")
    else:
        print(f"  {slug}: FAILED {r2.status_code}")

print(f"\nFixed {fixed} pages")
