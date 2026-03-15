"""
Center all feature rows on the homepage for better responsive/adaptive scaling.
Find all the feature section rows (two-column image+text) and add text-align:center
to the text columns, and center the images.
Also add responsive CSS so columns stack centered on tablet/mobile.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "home", "context": "edit", "_fields": "id,content"
}).json()
home = pages[0]
raw = home['content']['raw']

# Add responsive centering CSS to the existing aggressive padding CSS block
RESPONSIVE_CSS = '''
/* Feature rows - center content for adaptive scaling */
.wp-block-columns .wp-block-column h3,
.wp-block-columns .wp-block-column p {
    text-align: center !important;
}
.wp-block-columns .wp-block-column img {
    display: block !important;
    margin-left: auto !important;
    margin-right: auto !important;
}
@media (max-width: 782px) {
    .wp-block-columns {
        flex-direction: column !important;
        align-items: center !important;
    }
    .wp-block-column {
        flex-basis: 100% !important;
        width: 100% !important;
        max-width: 100% !important;
        text-align: center !important;
    }
    .wp-block-column img {
        max-width: 90% !important;
        margin: 0 auto 16px !important;
        display: block !important;
    }
    .wp-block-columns .wp-block-column p,
    .wp-block-columns .wp-block-column h3 {
        text-align: center !important;
    }
}
@media (max-width: 1024px) and (min-width: 783px) {
    .wp-block-columns .wp-block-column {
        text-align: center !important;
    }
    .wp-block-columns .wp-block-column img {
        max-width: 100% !important;
        margin: 0 auto !important;
        display: block !important;
    }
}
'''

# Find the aggressive padding CSS block and append responsive CSS
marker = '/* Aggressive top whitespace reduction */'
if marker in raw:
    # Find the end of the style block containing this marker
    marker_idx = raw.find(marker)
    # Find the </style> after the marker
    style_end = raw.find('</style>', marker_idx)
    if style_end > 0:
        # Check if we already added this
        if 'Feature rows - center content' not in raw:
            raw = raw[:style_end] + RESPONSIVE_CSS + raw[style_end:]
            print("Added responsive centering CSS")
        else:
            print("Responsive centering CSS already present")
    else:
        print("Could not find </style> after marker")
else:
    print("Aggressive padding CSS not found - checking alternative")
    # Try finding any style block with our custom CSS
    style_blocks = list(re.finditer(r'<style>(.*?)</style>', raw, re.DOTALL))
    for m in style_blocks:
        if 'Header Logo Size Override' in m.group():
            style_end = m.end() - len('</style>')
            raw = raw[:style_end] + RESPONSIVE_CSS + raw[style_end:]
            print("Added responsive centering CSS to logo style block")
            break

r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{home['id']}", json={"content": raw})
print(f"Update homepage: {r.status_code}")
if r.status_code == 200:
    print("Feature rows now centered for adaptive tablet/mobile scaling")
