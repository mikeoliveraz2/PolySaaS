"""
Add the standard header logo size + reduced padding CSS to the pricing page,
matching all other inner pages.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get a reference page (architecture) for the logo CSS block
pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
}).json()

logo_css_block = None
for p in pages:
    if p['slug'] == 'architecture':
        raw = p['content']['raw']
        for block in re.findall(r'(<!-- wp:html -->.*?<!-- /wp:html -->)', raw, re.DOTALL):
            if 'Header Logo Size Override' in block:
                clean = re.sub(r'</?p>', '', block)
                logo_css_block = clean
                print(f"Found logo CSS block ({len(clean)} chars)")
                break
        break

if not logo_css_block:
    print("Could not find logo CSS block!")
    sys.exit(1)

# Get pricing page
pricing = [p for p in pages if p['slug'] == 'pricing'][0]
raw = pricing['content']['raw']

# Check if it already has the logo CSS
if 'Header Logo Size Override' in raw:
    print("Pricing already has logo CSS - skipping")
    sys.exit(0)

# Insert the logo CSS block at the beginning of the page content
new_raw = logo_css_block + "\n\n" + raw

r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pricing['id']}", json={"content": new_raw})
print(f"Update pricing: {r.status_code}")
if r.status_code == 200:
    print("Pricing page now has standardized header logo + padding CSS")
