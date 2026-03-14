"""
Check where the dark mode toggle is on the About Us page.
"""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get About Us page
r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={"slug": "about-us", "_fields": "id,content"})
page = r.json()[0]
content = page['content']['rendered']

# Find all toggle-related content
for term in ['ps-theme-toggle', 'ps-dark-toggle', 'dark-mode', 'toggle', 'crescent', '☾']:
    positions = []
    start = 0
    while True:
        idx = content.find(term, start)
        if idx < 0:
            break
        positions.append(idx)
        start = idx + 1
    if positions:
        print(f"'{term}' found at positions: {positions}")
        for pos in positions[:3]:
            print(f"  ...{content[max(0,pos-80):pos+80]}...")
    else:
        print(f"'{term}' NOT found")

# Also check other pages that have a working toggle
print("\n=== Checking homepage for toggle ===")
r2 = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={"slug": "home", "_fields": "id,content"})
home = r2.json()[0]
home_content = home['content']['rendered']
if 'ps-theme-toggle' in home_content:
    idx = home_content.find('ps-theme-toggle')
    print(f"  Homepage has toggle at position {idx}")
else:
    print("  Homepage toggle NOT found")
if 'ps-dark-toggle' in home_content:
    print("  Homepage has ps-dark-toggle")

print("\nDone!")
