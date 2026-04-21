"""
Reduce excessive whitespace/padding across ALL pages.
Roughly halve large paddings to make the site feel tighter.
"""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

GRID_CSS = """
.wp-block-columns.is-layout-flex { display: flex !important; flex-wrap: wrap !important; flex-direction: row !important; gap: 20px; }
.wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 30% !important; min-width: 250px !important; max-width: 33% !important; word-wrap: break-word !important; overflow-wrap: break-word !important; }
@media (max-width: 900px) { .wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 45% !important; max-width: 48% !important; } }
@media (max-width: 600px) { .wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 100% !important; max-width: 100% !important; } }
.wp-block-column p, .wp-block-column h3 { word-wrap: break-word !important; overflow-wrap: break-word !important; white-space: normal !important; }
"""

# Padding reductions (old -> new)
PADDING_MAP = {
    "60px": "28px",
    "50px": "24px",
    "40px": "18px",
    "32px": "16px",
    "30px": "14px",
}

def reduce_padding(content, page_name):
    """Reduce large padding/margin values in inline styles."""
    changes = 0
    for old_val, new_val in PADDING_MAP.items():
        # Only replace padding-top and padding-bottom (not left/right)
        for prop in ['padding-top', 'padding-bottom', 'margin-top', 'margin-bottom']:
            old_str = f'{prop}:{old_val}'
            new_str = f'{prop}:{new_val}'
            count = content.count(old_str)
            if count > 0:
                content = content.replace(old_str, new_str)
                changes += count
    
    # Also handle "padding:Xpx Ypx" shorthand (top/bottom only - 4-value)
    # e.g. padding:60px 40px -> padding:28px 40px (only reduce top/bottom)
    
    print(f"  {page_name}: {changes} padding/margin reductions")
    return content

# Get all pages
r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={"per_page": 50})
pages = r.json()

print(f"Found {len(pages)} pages\n")

for page in pages:
    pid = page['id']
    slug = page['slug']
    content = page['content']['rendered']
    
    if not content.strip():
        continue
    
    original = content
    content = reduce_padding(content, slug)
    
    # Homepage: also ensure grid CSS
    if pid == 1313:
        if 'flex: 1 1 30%' not in content:
            content = content.replace('</style>', GRID_CSS + '\n</style>', 1)
            print("    Grid CSS re-added")
    
    if content != original:
        r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": content})
        status = 'OK' if r2.status_code == 200 else f'FAILED {r2.status_code}'
        print(f"    -> Updated: {status}")
    else:
        print(f"    -> No changes needed")

print("\nDone!")
