"""Center feature blocks - max specificity CSS approach."""
import requests, re, sys
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

# Remove old centering CSS
OLD_BLOCK = '''
/* Center Platform Features rows — target all column layouts after the heading */
.entry-content .wp-block-columns.are-vertically-aligned-center {
    max-width: 900px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}
'''
if OLD_BLOCK in raw:
    raw = raw.replace(OLD_BLOCK, '')
    print("  Removed old centering CSS")

# New approach: ultra-high specificity + target the WP container class
NEW_CSS = '''
/* Center Platform Features rows */
html body .site .entry-content .wp-block-columns.are-vertically-aligned-center.is-layout-flex,
html body .wp-block-columns.are-vertically-aligned-center.wp-block-columns-is-layout-flex,
.wp-container-core-columns-is-layout-b4fffc4a {
    max-width: 900px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    width: 100% !important;
    box-sizing: border-box !important;
}
'''

style_end = raw.find('</style>')
if style_end > 0 and 'Center Platform Features' not in raw:
    raw = raw[:style_end] + NEW_CSS + raw[style_end:]
    print("  Added high-specificity centering CSS")
elif 'Center Platform Features' in raw:
    print("  CSS already present")

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
            json={"content": raw}, timeout=30)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    print("  SUCCESS!")
else:
    print(f"  ERROR: {r2.text[:500]}")
