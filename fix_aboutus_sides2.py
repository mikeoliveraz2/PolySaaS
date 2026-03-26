"""Add CSS to About Us page to remove white side gaps."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/1345",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

fullwidth_css = """
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

# Find the first </style> in the page and insert before it
style_end = content.find('</style>')
if style_end > 0:
    content = content[:style_end] + fullwidth_css + content[style_end:]
    print("Injected full-width CSS into existing style block")
else:
    print("No </style> found!")
    sys.exit(1)

r2 = requests.post(BASE + "/wp-json/wp/v2/pages/1345",
                   auth=AUTH,
                   json={"content": content},
                   timeout=45)
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("SUCCESS - About Us white side gaps removed")
else:
    print(f"Error: {r2.text[:300]}")
