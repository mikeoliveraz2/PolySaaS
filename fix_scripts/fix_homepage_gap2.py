"""
Find the actual H2 title and on-page logo on the homepage, reduce gap between them.
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

# Find the wp:group blocks and wp:image blocks (Gutenberg blocks)
# The homepage structure should have: H2 title -> logo image -> hero text
# Look for wp:heading and wp:image blocks
for pattern in ['wp:heading', 'wp:image', 'wp:group']:
    indices = [m.start() for m in re.finditer(pattern, raw)]
    print(f"{pattern}: found at {indices[:5]}")

# Find the H2 "PolySaaS" or page title
h2_matches = list(re.finditer(r'<h2[^>]*>.*?</h2>', raw, re.DOTALL))
for m in h2_matches[:3]:
    text = re.sub(r'<[^>]+>', '', m.group()).strip()
    print(f"\nH2 at {m.start()}: '{text[:80]}'")
    # Show some context after
    after = raw[m.end():m.end()+300]
    print(f"  After: {after[:200]}")

# Find on-page logo img (not in CSS)
img_matches = list(re.finditer(r'<img[^>]*>', raw))
for m in img_matches[:5]:
    img = m.group()
    if 'logo' in img.lower() or 'polysaas' in img.lower():
        print(f"\nLogo img at {m.start()}: {img[:200]}")
        # Show context before
        before = raw[max(0,m.start()-200):m.start()]
        print(f"  Before: {before[-200:]}")

# Show content between CSS blocks and first real content (positions 3000-5000)
print(f"\n=== Chars 3000-5000 (after CSS, start of content) ===")
print(raw[3000:5000])
