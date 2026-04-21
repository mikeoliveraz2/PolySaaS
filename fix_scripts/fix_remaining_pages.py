"""Fix remaining pages - with retry and delay to avoid throttling."""
import requests, re, sys, time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

session = requests.Session()
retries = Retry(total=3, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

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

r = session.get(BASE + "/wp-json/wp/v2/pages",
                params={"status": "publish", "per_page": 50, "_fields": "id,title,slug"},
                auth=AUTH, timeout=30)
pages = r.json()
print(f"Found {len(pages)} published pages\n")

for page in pages:
    pid = page['id']
    title = page['title']['rendered']
    
    time.sleep(2)
    
    try:
        r2 = session.get(BASE + f"/wp-json/wp/v2/pages/{pid}",
                         params={"context": "edit", "_fields": "content"},
                         auth=AUTH, timeout=60)
    except Exception as e:
        print(f"  ERROR {title} (ID {pid}) - fetch: {e}")
        time.sleep(5)
        continue
    
    if r2.status_code != 200:
        print(f"  SKIP {title} (ID {pid}) - fetch status: {r2.status_code}")
        continue
    
    content = r2.json()["content"]["raw"]
    
    if MARKER in content:
        print(f"  SKIP {title} (ID {pid}) - already done")
        continue
    
    if not content.strip():
        print(f"  SKIP {title} (ID {pid}) - empty")
        continue

    style_end = content.find('</style>')
    if style_end > 0:
        new_content = content[:style_end] + FULLWIDTH_CSS + content[style_end:]
        method = "appended to existing <style>"
    else:
        new_content = f"<!-- wp:html --><style>{FULLWIDTH_CSS}</style><!-- /wp:html -->\n" + content
        method = "prepended new <style>"
    
    time.sleep(1)
    
    try:
        r3 = session.post(BASE + f"/wp-json/wp/v2/pages/{pid}",
                          auth=AUTH,
                          json={"content": new_content},
                          timeout=60)
        if r3.status_code == 200:
            print(f"  FIXED {title} (ID {pid}) - {method}")
        else:
            print(f"  ERROR {title} (ID {pid}) - update: {r3.status_code}")
    except Exception as e:
        print(f"  ERROR {title} (ID {pid}) - post: {e}")
        time.sleep(5)

print("\nDone!")
