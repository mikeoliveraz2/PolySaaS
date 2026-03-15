"""
Apply the same whitespace reduction to About Us that was done on the homepage:
1. Check current CSS state
2. Remove empty <p><br></p> spacers
3. Ensure aggressive padding CSS is present and complete
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "about-us", "context": "edit", "_fields": "id,content"
}).json()
about = pages[0]
raw = about['content']['raw']
print(f"About Us: {len(raw)} chars")

changes = 0

# 1. Remove empty <p><br /></p> spacers throughout
before_len = len(raw)
raw = re.sub(r'\s*<p><br\s*/?\s*>\s*</p>\s*', '\n', raw)
removed = before_len - len(raw)
if removed > 0:
    print(f"Removed empty <p><br></p> spacers ({removed} chars)")
    changes += 1

# 2. Remove empty <p></p> tags
before_len = len(raw)
raw = re.sub(r'\s*<p>\s*</p>\s*', '\n', raw)
removed = before_len - len(raw)
if removed > 0:
    print(f"Removed empty <p></p> tags ({removed} chars)")
    changes += 1

# 3. Check if the logo CSS block has the full aggressive whitespace CSS
# The homepage has these extra rules that About Us might be missing
has_aggressive = 'Aggressive top whitespace' in raw
has_homepage_specific = 'site-main > article' in raw
has_content_wrap = 'content-wrap' in raw and 'padding-top: 0' in raw

print(f"Has 'Aggressive' CSS: {has_aggressive}")
print(f"Has 'site-main > article': {has_homepage_specific}")
print(f"Has 'content-wrap' rule: {has_content_wrap}")

# Replace the logo CSS block with the full version matching homepage
FULL_CSS = '''<style>
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

# Find and replace the existing logo CSS wp:html block
blocks = re.findall(r'(<!-- wp:html -->.*?<!-- /wp:html -->)', raw, re.DOTALL)
for b in blocks:
    if 'Header Logo Size Override' in b:
        new_block = f"<!-- wp:html -->{FULL_CSS}<!-- /wp:html -->"
        raw = raw.replace(b, new_block, 1)
        print("Replaced logo/padding CSS block with full aggressive version")
        changes += 1
        break

if changes > 0:
    r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{about['id']}", json={"content": raw})
    print(f"\nUpdate About Us: {r.status_code}")
    if r.status_code == 200:
        print("About Us whitespace reduction applied (matching homepage)")
else:
    print("No changes needed")
