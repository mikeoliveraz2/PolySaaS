"""Fix nav menu colors on all pages that have nav CSS.
Dark mode: current=white, others=blue
Light mode: current=blue, others=black
"""
import requests, re, sys, time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

session = requests.Session()
retries = Retry(total=3, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

NAV_CSS = """
/* Nav menu: light mode - current=blue, others=black */
.header-navigation .menu > li > a,
.header-navigation .menu > li > a:visited {
    color: #000000 !important;
    font-weight: 500;
    font-size: 0.9rem;
}
.header-navigation .menu > li > a:hover {
    color: #2563EB !important;
}
.header-navigation .menu > li.current-menu-item > a,
.header-navigation .menu > li.current-menu-item > a:visited {
    color: #2563EB !important;
    font-weight: 600;
}
/* Nav menu: dark mode - current=white, others=blue */
body.dark-mode .header-navigation .menu > li > a,
body.dark-mode .header-navigation .menu > li > a:visited,
body.dark-mode .site-header .header-navigation a {
    color: #60A5FA !important;
}
body.dark-mode .header-navigation .menu > li > a:hover {
    color: #FFFFFF !important;
}
body.dark-mode .header-navigation .menu > li.current-menu-item > a,
body.dark-mode .header-navigation .menu > li.current-menu-item > a:visited {
    color: #FFFFFF !important;
    font-weight: 600;
}
"""

MARKER = "Nav menu: light mode - current=blue"

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
        print(f"  SKIP {title} (ID {pid}) - fetch: {r2.status_code}")
        continue
    
    content = r2.json()["content"]["raw"]
    
    if MARKER in content:
        print(f"  SKIP {title} (ID {pid}) - already done")
        continue
    
    if not content.strip():
        print(f"  SKIP {title} (ID {pid}) - empty")
        continue

    # Find the LAST </style> to append our overriding rules before it
    last_style = content.rfind('</style>')
    if last_style > 0:
        new_content = content[:last_style] + NAV_CSS + content[last_style:]
        method = "appended nav CSS"
    else:
        new_content = f"<!-- wp:html --><style>{NAV_CSS}</style><!-- /wp:html -->\n" + content
        method = "prepended nav CSS"
    
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
