"""Check dark mode blocks on one page"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
})
pages = {p['slug']: p for p in r.json()}

# Check architecture page
arch = pages['architecture']
raw = arch['content']['raw']

# Find all wp:html blocks
blocks = re.findall(r'<!-- wp:html -->(.*?)<!-- /wp:html -->', raw, re.DOTALL)
for i, block in enumerate(blocks):
    if 'body.dark-mode' in block:
        print(f"Block {i}: HAS dark mode CSS ({len(block)} chars)")
    elif 'ps-theme-toggle' in block:
        print(f"Block {i}: HAS toggle button ({len(block)} chars)")
    elif ':root' in block:
        print(f"Block {i}: HAS :root vars ({len(block)} chars)")
    else:
        content_preview = block[:100].replace('\n', ' ')
        print(f"Block {i}: OTHER ({len(block)} chars) - {content_preview}")

# Also check the homepage for reference
home = pages.get('home-2') or pages.get('home') or pages.get('industrial-strength-saas-for-limitless-horizons')
if home:
    print(f"\n--- HOMEPAGE (slug: {home['slug']}) ---")
    hraw = home['content']['raw']
    hblocks = re.findall(r'<!-- wp:html -->(.*?)<!-- /wp:html -->', hraw, re.DOTALL)
    for i, block in enumerate(hblocks):
        if 'body.dark-mode' in block:
            print(f"Block {i}: HAS dark mode CSS ({len(block)} chars)")
        elif 'ps-theme-toggle' in block:
            print(f"Block {i}: HAS toggle button ({len(block)} chars)")
        elif ':root' in block:
            print(f"Block {i}: HAS :root vars ({len(block)} chars)")
        else:
            content_preview = block[:100].replace('\n', ' ')
            print(f"Block {i}: OTHER ({len(block)} chars) - {content_preview}")
else:
    # Find homepage
    for slug in sorted(pages.keys()):
        print(f"  slug: {slug}")
