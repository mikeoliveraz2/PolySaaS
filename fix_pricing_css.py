"""
Inject dark mode CSS into the pricing page by pulling from a page that has it.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get a known-good page (architecture) for CSS blocks
pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
}).json()

css_blocks = []
toggle_block = ""

# Find CSS from any page that has it
for p in pages:
    raw = p['content']['raw']
    for block in re.findall(r'<!-- wp:html -->(.*?)<!-- /wp:html -->', raw, re.DOTALL):
        clean = re.sub(r'</?p>', '', block)
        if '<style' in clean and ('--ps-' in clean or 'body.dark-mode' in clean or '.ps-' in clean):
            if clean not in [re.sub(r'</?p>', '', b.replace('<!-- wp:html -->', '').replace('<!-- /wp:html -->', '')) for b in css_blocks]:
                css_blocks.append(f"<!-- wp:html -->{clean}<!-- /wp:html -->")
        if ('ps-dark-toggle' in clean or 'ps-theme-toggle' in clean) and not toggle_block:
            toggle_block = f"<!-- wp:html -->{clean}<!-- /wp:html -->"
    if css_blocks:
        print(f"Found CSS from page: {p['slug']} ({len(css_blocks)} blocks)")
        break

print(f"CSS blocks: {len(css_blocks)}, Toggle: {'yes' if toggle_block else 'no'}")

# Get current pricing page
pricing = [p for p in pages if p['slug'] == 'pricing'][0]
pricing_raw = pricing['content']['raw']

# Extract the pricing HTML content (non-CSS, non-toggle blocks)
pricing_content_blocks = []
for block in re.findall(r'(<!-- wp:html -->.*?<!-- /wp:html -->)', pricing_raw, re.DOTALL):
    inner = re.sub(r'<!-- /?wp:html -->', '', block).strip()
    if 'ps-dark-toggle' in inner or 'ps-theme-toggle' in inner:
        continue
    if '<style' in inner and ('--ps-' in inner or 'body.dark-mode' in inner):
        continue
    pricing_content_blocks.append(block)

print(f"Pricing content blocks: {len(pricing_content_blocks)}")

# Build new content
parts = css_blocks + ([toggle_block] if toggle_block else []) + pricing_content_blocks
new_content = "\n\n".join(parts)

r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pricing['id']}", json={
    "content": new_content
})
print(f"Update: {r.status_code}")
if r.status_code == 200:
    print("Pricing page updated with CSS + toggle + pricing content")
