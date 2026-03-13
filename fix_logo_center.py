"""
Fix homepage logo centering - inspect and fix.
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

r = s.get(f"{AZURE}/wp-json/wp/v2/pages/1313")
content = r.json()['content']['rendered']

# Find the logo image and its full surrounding context
logo_idx = content.find('Industrial-PolySaas-Cropped-300-Transparent')
if logo_idx < 0:
    logo_idx = content.find('PolySaaS-Industrial-Logo')
if logo_idx < 0:
    print("Logo image not found!")
    sys.exit(1)

# Get wide context around the logo
start = max(0, logo_idx - 500)
end = min(len(content), logo_idx + 300)
print(f"Logo area:\n{content[start:end]}\n")

# The fix: ensure the figure and its parent div center the image
# WordPress uses aligncenter on figure but the parent div may not center it

# Add CSS to force centering of the logo area
LOGO_CSS = """
.wp-block-image { text-align: center !important; }
.wp-block-image figure.aligncenter { margin-left: auto !important; margin-right: auto !important; display: block !important; text-align: center !important; }
.wp-block-image figure.aligncenter img { margin-left: auto !important; margin-right: auto !important; display: block !important; }
"""

if 'figure.aligncenter img' not in content:
    content = content.replace('</style>', LOGO_CSS + '\n</style>', 1)
    print("Added logo centering CSS")

# Ensure grid CSS
if 'flex: 1 1 30%' not in content:
    content = content.replace('</style>', GRID_CSS + '\n</style>', 1)
    print("Grid CSS re-added")

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/1313", json={"content": content})
print(f"Update: {'OK' if r2.status_code == 200 else f'FAILED {r2.status_code}'}")
print("Done!")
