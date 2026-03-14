"""
Fix top menu bar colors:
- Light mode: light grey background
- Dark mode: slightly lighter blue background
Applied to all pages via the dark mode CSS block.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get all pages
r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
})
all_pages = r.json()

# The CSS changes needed:
# Light mode header: change from #FFFFFF to light grey (#F1F5F9)
# Dark mode header: change from #0F172A to slightly lighter blue (#1E293B)

# We need to update the :root and body.dark-mode CSS vars
# --ps-header-bg in :root: #FFFFFF -> #F1F5F9
# --ps-header-bg in body.dark-mode: #0F172A -> #1E293B

# Also need to update the direct selectors for #masthead etc.

updated = 0
for page in all_pages:
    slug = page['slug']
    raw = page['content']['raw']
    
    changed = False
    new_raw = raw
    
    # Update :root --ps-header-bg from white to light grey
    if '--ps-header-bg: #FFFFFF' in new_raw:
        new_raw = new_raw.replace('--ps-header-bg: #FFFFFF', '--ps-header-bg: #F1F5F9')
        changed = True
    
    # Update body.dark-mode --ps-header-bg from very dark to slightly lighter blue
    if '--ps-header-bg: #0F172A' in new_raw:
        new_raw = new_raw.replace('--ps-header-bg: #0F172A', '--ps-header-bg: #1E293B')
        changed = True
    
    # Also update any direct background: #ffffff on masthead/site-header
    # The CSS has: background: #ffffff !important;
    if 'background: #ffffff !important' in new_raw:
        new_raw = new_raw.replace('background: #ffffff !important', 'background: #F1F5F9 !important')
        changed = True
    
    if changed:
        r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page['id']}", json={"content": new_raw})
        if r2.status_code == 200:
            updated += 1
            print(f"  {slug}: updated")
        else:
            print(f"  {slug}: FAILED {r2.status_code}")

print(f"\nUpdated {updated} pages")
