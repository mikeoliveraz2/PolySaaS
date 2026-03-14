"""Move toggle below header bar so it doesn't overlap Sign Up nav item.
Uses context=edit for raw content to preserve wp:html blocks."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from wp_snapshot import take_snapshot

take_snapshot("before toggle position fix")

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
})
pages = r.json()
print(f"Found {len(pages)} pages")

# The toggle was at top:80px originally, then moved to top:12px (overlapping nav).
# Move to top:90px;right:20px -- just below the ~80px header bar, clear of nav items.
POSITIONS_TO_FIX = [
    'position:fixed;top:12px;right:12px',
    'position:fixed;top:80px;right:20px',
]
NEW_POS = 'position:fixed;top:90px;right:20px'

fixed = 0
for page in pages:
    pid = page['id']
    slug = page['slug']
    raw = page['content']['raw']
    
    if not raw.strip():
        continue
    
    changed = False
    for old_pos in POSITIONS_TO_FIX:
        if old_pos in raw:
            raw = raw.replace(old_pos, NEW_POS)
            changed = True
    
    if changed:
        r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": raw})
        if r2.status_code == 200:
            fixed += 1
            print(f"  {slug}: moved toggle to top:90px")
        else:
            print(f"  {slug}: FAILED {r2.status_code}")

print(f"\nFixed {fixed} pages")
