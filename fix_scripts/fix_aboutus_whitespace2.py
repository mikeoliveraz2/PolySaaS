"""
Add page-specific gap reduction CSS to About Us, matching what homepage has with .home
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

PAGE_SPECIFIC_CSS = '''
/* About Us page-specific gap reduction */
.page .wp-block-group { margin-top: 0 !important; padding-top: 0 !important; }
.page .wp-block-image { margin-top: 0 !important; margin-bottom: 10px !important; }
.page .aligncenter { margin-top: 0 !important; }
.page figure.aligncenter { margin-top: 0 !important; margin-bottom: 10px !important; }
.page .entry-content > * { margin-top: 0 !important; }
.page .entry-content > *:first-child { margin-top: 0 !important; padding-top: 0 !important; }
.page .wp-block-columns .wp-block-column h3,
.page .wp-block-columns .wp-block-column p {
    text-align: center !important;
}
.page .wp-block-columns .wp-block-column img {
    display: block !important;
    margin-left: auto !important;
    margin-right: auto !important;
}
'''

# Find the aggressive padding CSS block and append
marker = '/* Aggressive top whitespace reduction */'
if marker in raw and 'About Us page-specific' not in raw:
    style_end = raw.find('</style>', raw.find(marker))
    if style_end > 0:
        raw = raw[:style_end] + PAGE_SPECIFIC_CSS + raw[style_end:]
        print("Added page-specific gap reduction CSS")
    
    # Also strip any remaining loose <p><br></p> and excessive newlines
    raw = re.sub(r'\n{3,}', '\n\n', raw)
    
    r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{about['id']}", json={"content": raw})
    print(f"Update: {r.status_code}")
else:
    if 'About Us page-specific' in raw:
        print("Already has page-specific CSS")
    else:
        print("Could not find marker")
