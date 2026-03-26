"""Fix feature block centering by adding CSS rules to the homepage style block.
WordPress layout classes override inline margin styles, so we need !important.
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

# First, revert the inline styles we added earlier (they're being overridden anyway)
raw = raw.replace(
    'margin-bottom:18px;max-width:900px;margin-left:auto;margin-right:auto',
    'margin-bottom:18px'
)
raw = raw.replace(
    'background-color:#F3F4F6;padding-top:8px;padding-bottom:10px;max-width:900px;margin-left:auto;margin-right:auto',
    'background-color:#F3F4F6;padding-top:8px;padding-bottom:10px'
)
print("  Reverted inline centering styles")

# Add CSS to the page's style block for centering feature rows
CENTER_CSS = '''
/* Center Platform Features rows */
#platform-features ~ .wp-block-columns {
    max-width: 900px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}
'''

# Find the style block on the page (Header Logo Size Override section)
style_end = raw.find('</style>')
if style_end > 0:
    if 'Center Platform Features' not in raw:
        raw = raw[:style_end] + CENTER_CSS + raw[style_end:]
        print("  Added centering CSS to style block")
    else:
        print("  Centering CSS already present")
else:
    print("  ERROR: No style block found on page")
    sys.exit(1)

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page_id}",
            json={"content": raw}, timeout=30)
print(f"  Status: {r2.status_code}")
if r2.status_code == 200:
    print("  SUCCESS! Feature blocks centered via CSS !important")
else:
    print(f"  ERROR: {r2.text[:500]}")
