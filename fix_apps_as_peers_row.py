"""
Flip the Apps As Peers row on the homepage so picture is on the right
and text is on the left (consistent with other rows).
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

# Find the Apps As Peers section
aap_idx = raw.find('Apps As Peers')
if aap_idx < 0:
    aap_idx = raw.find('Apps as Peers')
if aap_idx < 0:
    print("Apps As Peers not found!")
    sys.exit(1)

print(f"Found 'Apps As Peers' at position {aap_idx}")

# Find the row container - look for a flex row div before this text
# Show context around it
area_start = max(0, aap_idx - 600)
area_end = min(len(raw), aap_idx + 1500)
area = raw[area_start:area_end]
print(f"\nContext around Apps As Peers:")
print(area[:2000])
