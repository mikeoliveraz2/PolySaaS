"""
Reduce the gap between the title header and the logo on the homepage.
Check what's between them and tighten the spacing.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "home", "context": "edit", "_fields": "id,content"
}).json()
if not pages:
    pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
        "slug": "home-3", "context": "edit", "_fields": "id,content"
    }).json()

home = pages[0]
raw = home['content']['raw']

# Find the H2 page title and the logo image to see what's between them
h2_idx = raw.find('<h2')
logo_idx = raw.find('polysaas-logo')
if logo_idx < 0:
    logo_idx = raw.find('custom-logo')
if logo_idx < 0:
    logo_idx = raw.find('wp-image')

print(f"H2 at: {h2_idx}")
print(f"Logo at: {logo_idx}")

if h2_idx >= 0 and logo_idx >= 0:
    between = raw[h2_idx:logo_idx]
    print(f"\nBetween H2 and logo ({len(between)} chars):")
    print(between[:1000])

# Also check the first 3000 chars of homepage to understand structure
print(f"\n=== First 2000 chars of homepage ===")
print(raw[:2000])
