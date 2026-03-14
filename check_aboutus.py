"""Check the About Us page content structure"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content,title"
})
pages = {p['slug']: p for p in r.json()}

about = pages['about-us']
raw = about['content']['raw']

# Find all wp:html blocks and show their content summaries
blocks = re.findall(r'(<!-- wp:html -->.*?<!-- /wp:html -->)', raw, re.DOTALL)
print(f"About Us page has {len(blocks)} wp:html blocks\n")

for i, block in enumerate(blocks):
    # Strip the wp:html wrappers
    inner = block.replace('<!-- wp:html -->', '').replace('<!-- /wp:html -->', '').strip()
    
    if '<style>' in inner:
        # CSS block - just summarize
        if 'body.dark-mode' in inner:
            print(f"Block {i}: CSS - Dark mode system ({len(inner)} chars)")
        elif 'Header Logo' in inner:
            print(f"Block {i}: CSS - Header logo + padding ({len(inner)} chars)")
        else:
            print(f"Block {i}: CSS - Other ({len(inner)} chars)")
    elif 'ps-theme-toggle' in inner:
        print(f"Block {i}: Toggle button")
    else:
        # Content block - show text
        text = re.sub(r'<[^>]+>', ' ', inner)
        text = re.sub(r'\s+', ' ', text).strip()
        print(f"Block {i}: Content ({len(inner)} chars)")
        # Show first 300 chars
        print(f"  {text[:400]}")
        print()
