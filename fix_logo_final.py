"""
Fix header logo by working with RAW content (context=edit) to preserve wp:html blocks.
The issue: previous scripts fetched content.rendered (wpautop-corrupted) and posted it back,
stripping the <!-- wp:html --> protection.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

HEADER_LOGO_CSS = """/* PolySaaS Header Logo Size Override */
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
}"""

CSS_BLOCK = f'<!-- wp:html -->\n<style>\n{HEADER_LOGO_CSS}\n</style>\n<!-- /wp:html -->'

# Fetch pages with context=edit to get RAW content
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
    
    original = raw
    
    # Remove any existing corrupted header logo CSS blocks
    # Pattern: look for the Header Logo Size Override comment and remove the entire wp:html block
    # Also remove any standalone (non wp:html wrapped) version
    
    # Remove wp:html wrapped versions
    raw = re.sub(
        r'<!-- wp:html -->\s*<style>\s*/\* PolySaaS Header Logo Size Override \*/.*?</style>\s*<!-- /wp:html -->',
        '', raw, flags=re.DOTALL
    )
    
    # Remove any corrupted standalone versions
    raw = re.sub(
        r'<style>\s*/\* PolySaaS Header Logo Size Override \*/.*?</style>',
        '', raw, flags=re.DOTALL
    )
    
    # Also remove broken versions with <p> tags
    raw = re.sub(
        r'<p>/\* PolySaaS Header Logo Size Override \*/.*?</p>',
        '', raw, flags=re.DOTALL
    )
    
    # Clean up any empty wp:html blocks left behind
    raw = re.sub(r'<!-- wp:html -->\s*<!-- /wp:html -->', '', raw)
    
    # Prepend the clean CSS block
    raw = CSS_BLOCK + '\n' + raw.lstrip()
    
    if raw != original:
        r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": raw})
        if r2.status_code == 200:
            fixed += 1
            print(f"  {slug}: fixed (raw content)")
        else:
            print(f"  {slug}: FAILED {r2.status_code} - {r2.text[:200]}")

print(f"\nFixed {fixed} pages")

# Verify by checking rendered HTML
print("\n=== Verifying rendered output ===")
r3 = requests.get(f"{AZURE}?nocache={fixed}")
html = r3.text

styles = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
for i, st in enumerate(styles):
    if 'Header Logo Size Override' in st:
        print(f"  Style block {i}: Found header logo CSS")
        if '<p>' in st:
            print(f"  WARNING: Still corrupted with <p> tags!")
        else:
            print(f"  Clean CSS - no <p> corruption!")
        # Show the actual max-width line
        for line in st.split('\n'):
            if 'max-width' in line and '60px' in line:
                print(f"  Rule: {line.strip()}")

# Also check Kadence default
kadence = re.findall(r'\.site-branding a\.brand img\{[^}]*\}', html)
print(f"\n  Kadence default rules: {len(kadence)}")
for k in kadence:
    print(f"    {k[:200]}")

print("\nDone!")
