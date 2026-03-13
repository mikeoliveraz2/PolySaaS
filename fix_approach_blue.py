"""
Fix "Our Approach" heading to bright blue. Inspect current HTML first.
"""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

s = requests.Session()
s.auth = (USER, APP_PASS)

BRIGHT_BLUE = "#2563EB"

GRID_CSS = """
.wp-block-columns.is-layout-flex { display: flex !important; flex-wrap: wrap !important; flex-direction: row !important; gap: 20px; }
.wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 30% !important; min-width: 250px !important; max-width: 33% !important; word-wrap: break-word !important; overflow-wrap: break-word !important; }
@media (max-width: 900px) { .wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 45% !important; max-width: 48% !important; } }
@media (max-width: 600px) { .wp-block-columns.is-layout-flex > .wp-block-column { flex: 1 1 100% !important; max-width: 100% !important; } }
.wp-block-column p, .wp-block-column h3 { word-wrap: break-word !important; overflow-wrap: break-word !important; white-space: normal !important; }
"""

r = s.get(f"{AZURE}/wp-json/wp/v2/pages/1313")
content = r.json()['content']['rendered']

# Find "Our Approach" exact context
idx = content.find('Our Approach')
if idx < 0:
    print("ERROR: 'Our Approach' not found on homepage!")
else:
    snippet = content[max(0, idx-250):idx+100]
    print(f"Our Approach context:\n{snippet}\n")
    
    # Find the opening tag for this heading
    tag_start = content.rfind('<h', 0, idx)
    tag_end = content.find('>', tag_start) + 1
    heading_end = content.find('</h', idx)
    close_end = content.find('>', heading_end) + 1
    
    old_heading = content[tag_start:close_end]
    print(f"Full heading tag: {old_heading}")
    
    # Add color to the style attribute
    if f'color:{BRIGHT_BLUE}' in old_heading:
        print("Already has bright blue!")
    elif 'style="' in old_heading:
        new_heading = old_heading.replace('style="', f'style="color:{BRIGHT_BLUE} !important;')
        content = content.replace(old_heading, new_heading)
        print(f"Fixed -> {new_heading}")
    else:
        # Add style attribute
        new_heading = old_heading.replace('>', f' style="color:{BRIGHT_BLUE} !important">', 1)
        content = content.replace(old_heading, new_heading)
        print(f"Fixed -> {new_heading}")

# Ensure grid CSS
if 'flex: 1 1 30%' not in content:
    content = content.replace('</style>', GRID_CSS + '\n</style>', 1)
    print("Grid CSS re-added")

# Save
r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/1313", json={"content": content})
print(f"\nHomepage update: {'OK' if r2.status_code == 200 else f'FAILED {r2.status_code}'}")

# Verify
r3 = s.get(f"{AZURE}/wp-json/wp/v2/pages/1313")
final = r3.json()['content']['rendered']
idx2 = final.find('Our Approach')
if idx2 > 0:
    ts = final.rfind('<h', 0, idx2)
    te = final.find('>', final.find('</h', idx2)) + 1
    print(f"Verified: {final[ts:te]}")

print("\nDone!")
