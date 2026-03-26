"""Fix feature block centering - use broader CSS selectors and check DOM structure."""
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

# Remove the old CSS attempt
OLD_CSS = '''
/* Center Platform Features rows */
#platform-features ~ .wp-block-columns {
    max-width: 900px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}
'''
if OLD_CSS in raw:
    raw = raw.replace(OLD_CSS, '')
    print("  Removed old CSS attempt")

# Instead, wrap the feature rows in a centered container div
# Find the Platform Features heading and the section end
pf_heading = raw.find('id="platform-features"')
heading_line_start = raw.rfind('<h2', max(0, pf_heading - 50), pf_heading)

# Find the CTA/footer section that ends the features
footer_start = raw.find('Stop Managing Tools')
footer_div_start = raw.rfind('<!--', max(0, footer_start - 200), footer_start)
if footer_div_start < 0:
    footer_div_start = raw.rfind('<div', max(0, footer_start - 200), footer_start)

# Show context around these positions
print(f"  Features heading at: {heading_line_start}")
print(f"  Footer starts around: {footer_div_start}")
print(f"  Content between: {footer_div_start - heading_line_start} chars")

# Add a wrapper div with centering around ALL feature rows
# We'll add max-width directly on each wp-block-columns div using a style tag approach
# that's more specific

NEW_CSS = '''
/* Center Platform Features rows — target all column layouts after the heading */
.entry-content .wp-block-columns.are-vertically-aligned-center {
    max-width: 900px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}
'''

style_end = raw.find('</style>')
if style_end > 0 and 'Center Platform Features' not in raw:
    raw = raw[:style_end] + NEW_CSS + raw[style_end:]
    print("  Added broad centering CSS")
elif 'Center Platform Features' in raw:
    print("  Centering CSS already present (skipped)")

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
            json={"content": raw}, timeout=30)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    print("  SUCCESS!")
else:
    print(f"  ERROR: {r2.text[:500]}")
