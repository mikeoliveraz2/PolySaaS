"""Scan all published pages and inject dark mode full-width CSS where missing."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

FULLWIDTH_CSS = """
/* Full-width: remove boxed content white side gaps */
.entry.single-entry,
.content-style-boxed .entry.single-entry {
    max-width: 100% !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    box-shadow: none !important;
}
.entry-content-wrap {
    max-width: 1290px !important;
    margin: 0 auto !important;
}
body.dark-mode .entry.single-entry,
body.dark-mode .entry-content-wrap,
body.dark-mode .content-style-boxed .entry.single-entry {
    background-color: var(--ps-bg, #0F172A) !important;
    background: var(--ps-bg, #0F172A) !important;
    box-shadow: none !important;
}
body.dark-mode #wrapper,
body.dark-mode .site,
body.dark-mode #main,
body.dark-mode .site-container,
body.dark-mode .content-area,
body.dark-mode .site-main {
    background-color: var(--ps-bg, #0F172A) !important;
    background: var(--ps-bg, #0F172A) !important;
}
"""

MARKER = "remove boxed content white side gaps"

# Get all published pages
r = requests.get(BASE + "/wp-json/wp/v2/pages",
                 params={"status": "publish", "per_page": 50, "_fields": "id,title,slug"},
                 auth=AUTH, timeout=30)
pages = r.json()
print(f"Found {len(pages)} published pages\n")

for page in pages:
    pid = page['id']
    title = page['title']['rendered']
    slug = page['slug']
    
    r2 = requests.get(BASE + f"/wp-json/wp/v2/pages/{pid}",
                      params={"context": "edit", "_fields": "content"},
                      auth=AUTH, timeout=45)
    if r2.status_code != 200:
        print(f"  SKIP {title} (ID {pid}) - fetch failed: {r2.status_code}")
        continue
    
    content = r2.json()["content"]["raw"]
    
    if MARKER in content:
        print(f"  SKIP {title} (ID {pid}) - already has full-width CSS")
        continue
    
    if not content.strip():
        print(f"  SKIP {title} (ID {pid}) - empty content")
        continue

    # Find a place to inject: existing <style> block or prepend new one
    style_end = content.find('</style>')
    if style_end > 0:
        new_content = content[:style_end] + FULLWIDTH_CSS + content[style_end:]
        method = "appended to existing <style>"
    else:
        new_content = f"<!-- wp:html --><style>{FULLWIDTH_CSS}</style><!-- /wp:html -->\n" + content
        method = "prepended new <style>"
    
    r3 = requests.post(BASE + f"/wp-json/wp/v2/pages/{pid}",
                       auth=AUTH,
                       json={"content": new_content},
                       timeout=45)
    if r3.status_code == 200:
        print(f"  FIXED {title} (ID {pid}) - {method}")
    else:
        print(f"  ERROR {title} (ID {pid}) - update failed: {r3.status_code}")

print("\nDone!")
