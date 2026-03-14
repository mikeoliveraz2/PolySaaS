import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "about-us", "context": "edit", "_fields": "id,slug,content"
}).json()
raw = pages[0]['content']['raw']

# Search for timeline-related content
for kw in ['Timeline', 'Futures', 'Q1 2025', 'Q1 2026', 'Platform Foundation', 'roadmap']:
    idx = raw.find(kw)
    if idx >= 0:
        print(f"Found '{kw}' at position {idx}")
        print(f"  Context: ...{raw[max(0,idx-80):idx+120]}...")
        print()

# Show the last 3000 chars of the page to see the bottom section
print("=== LAST 3000 chars of About Us ===")
print(raw[-3000:])
