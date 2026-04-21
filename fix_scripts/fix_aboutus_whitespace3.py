"""
Aggressively remove the Kadence page title hero band on About Us.
The theme renders a separate grey hero section with "About Us" that adds 
massive whitespace. Hide it or collapse it completely.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "about-us", "context": "edit", "_fields": "id,content"
}).json()
about = pages[0]
raw = about['content']['raw']

# Nuclear option: hide the entire Kadence page title/hero section
HERO_KILL_CSS = '''
/* Kill the Kadence page title hero section completely */
.entry-hero-container-inner,
.entry-hero-layout-contain,
.entry-hero,
.page-hero-section,
.entry-hero-section,
.kadence-page-hero,
.hero-section-overlay,
.entry-hero-section-overlay,
.wp-block-kadence-hero {
    display: none !important;
    height: 0 !important;
    max-height: 0 !important;
    overflow: hidden !important;
    padding: 0 !important;
    margin: 0 !important;
    min-height: 0 !important;
}
/* Also target the title inside it */
.entry-hero h1.entry-title,
.entry-hero .entry-header,
.page .entry-hero-container {
    display: none !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}
/* Remove any gap between header and content */
.site-main {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
.content-area {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
#inner-wrap {
    padding-top: 0 !important;
}
.site-content .content-area {
    padding-top: 0 !important;
    margin-top: 0 !important;
}
'''

# Find existing aggressive CSS and add hero kill rules
if 'Kill the Kadence page title hero' not in raw:
    marker = '/* Aggressive top whitespace reduction */'
    if marker in raw:
        style_end = raw.find('</style>', raw.find(marker))
        if style_end > 0:
            raw = raw[:style_end] + HERO_KILL_CSS + raw[style_end:]
            print("Added hero section kill CSS")
    
    r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{about['id']}", json={"content": raw})
    print(f"Update: {r.status_code}")
else:
    print("Hero kill CSS already present")
