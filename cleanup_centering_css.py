"""Remove all centering CSS attempts from the homepage content."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages",
          params={"slug": "home", "context": "edit", "_fields": "id,content"},
          timeout=30)
page = r.json()[0]
raw = page['content']['raw']
page_id = page['id']
print(f"Page ID: {page_id}, length: {len(raw)} chars")

# Remove the content area centering CSS block
CSS_BLOCK = '''
/* Center page content area on wide screens */
.entry-content-wrap {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
}
.entry-content-wrap > * {
    width: 100% !important;
    max-width: 1200px !important;
}
'''
if CSS_BLOCK in raw:
    raw = raw.replace(CSS_BLOCK, '')
    print("  Removed 'Center page content area' CSS")

# Also remove wrapper div if it's still there
if 'ps-features-centered' in raw:
    raw = raw.replace(
        '<div class="ps-features-centered" style="max-width:900px;margin:0 auto;padding:0 20px;">',
        ''
    )
    print("  Removed wrapper div opening tag")

# Verify no centering remnants
for term in ['Center Platform Features', 'Center page content', 'ps-features-centered']:
    if term in raw:
        print(f"  WARNING: '{term}' still found in content")
    else:
        print(f"  Clean: no '{term}'")

print(f"\n  New length: {len(raw)} chars")
r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
            json={"content": raw}, timeout=30)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    print("  SUCCESS! All centering CSS cleaned up.")
else:
    print(f"  ERROR: {r2.text[:500]}")
