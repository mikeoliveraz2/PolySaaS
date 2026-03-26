"""Center feature blocks by wrapping them in a max-width container div.
Instead of fighting CSS specificity, wrap the rows in a centered div.
"""
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

# Remove old centering CSS attempts
OLD_CSS = '''
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
if OLD_CSS in raw:
    raw = raw.replace(OLD_CSS, '')
    print("  Removed old CSS")

# Check if we already wrapped it
if 'ps-features-centered' in raw:
    print("  Already wrapped — aborting")
    sys.exit(0)

# Find the Platform Features heading
pf_idx = raw.find('Platform Features</h2>')
if pf_idx < 0:
    print("  ERROR: Platform Features heading not found")
    sys.exit(1)

# The heading tag starts before
h2_start = raw.rfind('<h2', max(0, pf_idx - 100), pf_idx)
h2_end = pf_idx + len('Platform Features</h2>')
print(f"  Platform Features <h2> at {h2_start}:{h2_end}")

# Find where the features end - look for the footer/CTA "Stop Managing Tools"
footer_marker = 'Stop Managing Tools'
footer_idx = raw.find(footer_marker, h2_end)
if footer_idx < 0:
    print("  ERROR: Could not find end of features section")
    sys.exit(1)

# Go back to find the start of the footer section
# It should be a wp:html block or similar
footer_block_start = raw.rfind('<!-- wp:html -->', max(h2_end, footer_idx - 500), footer_idx)
if footer_block_start < 0:
    footer_block_start = raw.rfind('<div', max(h2_end, footer_idx - 200), footer_idx)

print(f"  Features content: {h2_end} to {footer_block_start}")

# Extract just the feature rows (between heading and footer)
feature_rows = raw[h2_end:footer_block_start]
print(f"  Feature rows: {len(feature_rows)} chars")

# Wrap in a centered container
wrapped = f'\n<div class="ps-features-centered" style="max-width:900px;margin:0 auto;padding:0 20px;">{feature_rows}</div>\n'

raw = raw[:h2_end] + wrapped + raw[footer_block_start:]

print(f"\n=== Updating page (new length: {len(raw)} chars) ===")
r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
            json={"content": raw}, timeout=30)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    print("  SUCCESS! Feature rows wrapped in centered container")
else:
    print(f"  ERROR: {r2.text[:500]}")
