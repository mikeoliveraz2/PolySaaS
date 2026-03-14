"""
1. Re-inject header logo size CSS (lost during style block fixes)
2. Move toggle button so it doesn't overlap Sign Up menu item
"""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Check if header logo CSS is still present
print("=== Checking header logo CSS ===")
r = s.get(f"{AZURE}")
html = r.text
if 'Header Logo Size Override' in html:
    print("  Header logo CSS is present")
else:
    print("  Header logo CSS is MISSING - needs re-injection")

if 'max-width: 60px' in html or 'max-width:60px' in html:
    print("  max-width:60px found")
else:
    print("  max-width:60px NOT found")

# Fix toggle position: move from top:80px to top:12px and right:20px to avoid nav overlap
# Current: position:fixed;top:80px;right:20px
# The Sign Up is the last nav item, toggle at right:20px overlaps it
# Move toggle below the header bar instead

OLD_TOGGLE_POS = 'position:fixed;top:80px;right:20px'
NEW_TOGGLE_POS = 'position:fixed;top:12px;right:12px'

r2 = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={"per_page": 100, "_fields": "id,slug,content"})
pages = r2.json()
print(f"\nFound {len(pages)} pages")

HEADER_LOGO_CSS_BLOCK = '''<!-- wp:html -->
<style>
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
</style>
<!-- /wp:html -->'''

fixed = 0
for page in pages:
    pid = page['id']
    slug = page['slug']
    content = page['content']['rendered']
    
    if not content.strip():
        continue
    
    original = content
    
    # Fix 1: Re-inject header logo CSS if missing
    if 'Header Logo Size Override' not in content:
        # Prepend the CSS block
        content = HEADER_LOGO_CSS_BLOCK + '\n' + content
        print(f"  {slug}: re-injected header logo CSS")
    
    # Fix 2: Move toggle position
    if OLD_TOGGLE_POS in content:
        content = content.replace(OLD_TOGGLE_POS, NEW_TOGGLE_POS)
        print(f"  {slug}: moved toggle position")
    
    if content != original:
        r3 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": content})
        if r3.status_code == 200:
            fixed += 1
        else:
            print(f"  {slug}: FAILED {r3.status_code}")

print(f"\nFixed {fixed} pages")

# Verify
print("\n=== Verifying ===")
r4 = s.get(f"{AZURE}")
html2 = r4.text
if 'max-width: 60px' in html2 or 'max-width:60px' in html2:
    print("  Header logo CSS: VERIFIED")
else:
    print("  Header logo CSS: STILL MISSING")

if 'top:12px;right:12px' in html2:
    print("  Toggle position: VERIFIED")
else:
    print("  Toggle position: NOT updated")

print("Done!")
