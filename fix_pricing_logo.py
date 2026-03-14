"""
Standardize pricing page header logo size to match other inner pages.
Check what CSS other pages have and ensure pricing matches.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
}).json()

# Check a known-good inner page for logo CSS
for p in pages:
    if p['slug'] == 'architecture':
        raw = p['content']['raw']
        for block in re.findall(r'<!-- wp:html -->(.*?)<!-- /wp:html -->', raw, re.DOTALL):
            if 'custom-logo' in block or 'site-logo' in block or 'header-logo' in block or '.custom-logo-link' in block:
                print(f"=== Logo CSS from {p['slug']} ===")
                # Show relevant CSS lines
                for line in block.split('\n'):
                    if 'logo' in line.lower() or 'header' in line.lower() or 'max-width' in line.lower() or 'max-height' in line.lower():
                        print(f"  {line.strip()}")
                print(f"\n--- Full block ({len(block)} chars) ---")
                print(block[:800])
                print("...")
                break

# Check pricing page
pricing = [p for p in pages if p['slug'] == 'pricing'][0]
raw = pricing['content']['raw']
print(f"\n=== Pricing page blocks ===")
blocks = re.findall(r'<!-- wp:html -->(.*?)<!-- /wp:html -->', raw, re.DOTALL)
for i, b in enumerate(blocks):
    summary = b.strip()[:150].replace('\n', ' ')
    has_logo = 'logo' in b.lower()
    print(f"  Block {i}: {summary}... [logo:{has_logo}]")
