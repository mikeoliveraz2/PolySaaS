"""More aggressive padding reduction - set to near-zero"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

OLD_CSS = """/* Reduce top whitespace on all pages */
.content-area { margin-top: 1rem !important; margin-bottom: 2rem !important; }
.entry-content-wrap { padding-top: 0.5rem !important; }
.entry-hero-container-inner { padding-top: 0 !important; padding-bottom: 0 !important; min-height: 0 !important; }
.entry-hero .entry-header { min-height: 0 !important; padding: 10px 0 !important; }
h1.entry-title, .entry-hero h1 { margin-top: 0 !important; margin-bottom: 8px !important; padding-top: 0 !important; }
.content-bg { padding-top: 0 !important; }
"""

NEW_CSS = """/* Reduce top whitespace on all pages */
.content-area { margin-top: 0 !important; margin-bottom: 2rem !important; }
.entry-content-wrap { padding-top: 0 !important; }
.entry-hero-container-inner { padding-top: 0 !important; padding-bottom: 0 !important; min-height: 0 !important; display: none !important; }
.entry-hero .entry-header { min-height: 0 !important; padding: 0 !important; display: none !important; }
.page-hero-section { display: none !important; }
h1.entry-title, .entry-hero h1 { display: none !important; }
.content-bg { padding-top: 0 !important; }
.site-main { padding-top: 0 !important; }
"""

r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
})
pages = r.json()
print(f"Found {len(pages)} pages")

fixed = 0
for page in pages:
    pid = page['id']
    slug = page['slug']
    raw = page['content']['raw']
    
    if not raw.strip():
        continue
    
    if OLD_CSS in raw:
        raw = raw.replace(OLD_CSS, NEW_CSS)
        r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": raw})
        if r2.status_code == 200:
            fixed += 1
            print(f"  {slug}: padding updated")
        else:
            print(f"  {slug}: FAILED {r2.status_code}")

print(f"\nFixed {fixed} pages")
