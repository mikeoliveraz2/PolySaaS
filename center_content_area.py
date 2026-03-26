"""Center the page content wrapper so all content (including feature blocks) is centered.
The Kadence theme's content area is left-aligned on wide screens.
"""
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

# Remove previous centering CSS that targeted wp-block-columns
OLD_CSS = '''
/* Center Platform Features rows on wide screens */
.wp-block-columns.are-vertically-aligned-center {
    max-width: 1100px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}
.entry-content > .wp-block-columns,
.entry-content-wrap .wp-block-columns {
    max-width: 1100px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}
'''
if OLD_CSS in raw:
    raw = raw.replace(OLD_CSS, '')
    print("  Removed old CSS")

# New approach: center the entire content area AND the feature blocks
NEW_CSS = '''
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

style_end = raw.find('</style>')
if style_end > 0 and 'Center page content area' not in raw:
    raw = raw[:style_end] + NEW_CSS + raw[style_end:]
    print("  Added content area centering CSS")

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
            json={"content": raw}, timeout=30)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    print("  SUCCESS!")
else:
    print(f"  ERROR: {r2.text[:500]}")
