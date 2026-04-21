"""
Aggressively reduce top whitespace/padding across all published pages.
Check current CSS and add stronger overrides.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# First check what the current padding CSS looks like on a reference page
pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content,status"
}).json()

published = [p for p in pages if p.get('status') == 'publish']

# Check current padding rules on architecture page
for p in published:
    if p['slug'] == 'architecture':
        raw = p['content']['raw']
        for block in re.findall(r'<!-- wp:html -->(.*?)<!-- /wp:html -->', raw, re.DOTALL):
            if 'entry-hero' in block or 'content-area' in block or 'padding' in block.lower():
                if '<style' in block:
                    print(f"Current padding CSS from {p['slug']}:")
                    # Extract just the padding-related rules
                    for line in block.split('\n'):
                        line = line.strip()
                        if any(kw in line.lower() for kw in ['margin', 'padding', 'height', 'entry', 'content', 'hero', 'header', 'title']):
                            print(f"  {line}")
        break

# More aggressive padding override CSS
AGGRESSIVE_PADDING_CSS = '''<style>
/* PolySaaS Header Logo Size Override */
.site-branding a.brand img,
.site-branding a.brand img.custom-logo,
#masthead .site-branding a.brand img,
.site-header .site-branding a.brand img {
    max-width: 60px !important;
    max-height: 60px !important;
    width: auto !important;
    height: auto !important;
}
.site-branding .brand {
    max-width: 80px !important;
}
.mobile-site-branding a.brand img,
.mobile-site-branding a.brand img.custom-logo {
    max-width: 50px !important;
    max-height: 50px !important;
}

/* Aggressive top whitespace reduction */
.content-area { margin-top: 0 !important; padding-top: 0 !important; }
.entry-content-wrap { padding-top: 0 !important; margin-top: 0 !important; }
.entry-hero-container-inner { padding: 0 !important; min-height: 0 !important; }
.entry-hero .entry-header { min-height: 0 !important; padding: 5px 0 !important; margin: 0 !important; }
.entry-hero-container { min-height: 0 !important; padding: 0 !important; margin: 0 !important; }
.wp-site-blocks > .entry-content { margin-top: 0 !important; padding-top: 0 !important; }
.site-main { padding-top: 0 !important; margin-top: 0 !important; }
.site-content { padding-top: 0 !important; }
.hentry { margin-top: 0 !important; }
.entry-content { margin-top: 0 !important; padding-top: 0 !important; }
#inner-wrap > .content-area { margin-top: 0 !important; }
.page .entry-header { padding: 5px 0 !important; margin: 0 !important; min-height: 0 !important; }
.page .entry-hero-section { padding: 0 !important; margin: 0 !important; min-height: 0 !important; }
.entry-hero-section-overlay { padding: 0 !important; min-height: 0 !important; }
.hero-section-overlay { padding: 0 !important; min-height: 0 !important; }
.page-hero-section { padding: 0 !important; margin: 0 !important; }
.kadence-page-hero { padding: 0 !important; margin: 0 !important; min-height: 0 !important; }
.wp-block-post-title { margin-top: 0 !important; padding-top: 5px !important; }
.entry-title { margin-top: 0 !important; padding-top: 5px !important; margin-bottom: 5px !important; }
header.entry-header { padding-top: 0 !important; padding-bottom: 0 !important; }
.site-main > article { margin-top: 0 !important; padding-top: 0 !important; }
.site-container > .site-content { padding-top: 0 !important; }
.content-wrap { padding-top: 0 !important; }
</style>'''

updated = 0
for p in published:
    raw = p['content']['raw']
    
    # Find existing logo/padding CSS block and replace it
    old_block = None
    blocks = re.findall(r'(<!-- wp:html -->.*?<!-- /wp:html -->)', raw, re.DOTALL)
    for b in blocks:
        if 'Header Logo Size Override' in b:
            old_block = b
            break
    
    if old_block:
        new_block = f"<!-- wp:html -->{AGGRESSIVE_PADDING_CSS}<!-- /wp:html -->"
        new_raw = raw.replace(old_block, new_block, 1)
        r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{p['id']}", json={"content": new_raw})
        status = "OK" if r.status_code == 200 else f"ERR:{r.status_code}"
        print(f"  {p['slug']}: {status}")
        updated += 1
    else:
        print(f"  {p['slug']}: NO logo/padding block found - skipping")

print(f"\nUpdated {updated} pages with aggressive whitespace reduction")
