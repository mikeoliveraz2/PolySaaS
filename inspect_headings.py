import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

s = requests.Session()
s.auth = (USER, APP_PASS)

r = s.get(f"{AZURE}/wp-json/wp/v2/pages/1313")
content = r.json()['content']['rendered']

# Find all headings
headings = re.findall(r'<h[1-6][^>]*>.*?</h[1-6]>', content, re.DOTALL)
print(f"Found {len(headings)} headings:\n")
for i, h in enumerate(headings):
    text = re.sub(r'<[^>]+>', '', h).strip()
    tag = h[:h.find('>')+1]
    print(f"  {i+1}. [{tag[:80]}] -> \"{text[:80]}\"")

# Also search for "Approach" anywhere
idx = content.lower().find('approach')
if idx >= 0:
    print(f"\n'approach' found at {idx}: ...{content[max(0,idx-50):idx+80]}...")
else:
    print("\n'approach' not found anywhere on the page")

# Search for "Problem"
idx2 = content.find('Problem')
if idx2 >= 0:
    print(f"'Problem' found at {idx2}")
