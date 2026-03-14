import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "about-us", "context": "edit", "_fields": "id,slug,content"
}).json()
about = pages[0]
raw = about['content']['raw']

blocks = re.findall(r'(<!-- wp:html -->.*?<!-- /wp:html -->)', raw, re.DOTALL)
print(f"About Us: {len(blocks)} blocks, {len(raw)} chars total\n")

for i, b in enumerate(blocks):
    text = re.sub(r'<[^>]+>', ' ', b)
    text = re.sub(r'\s+', ' ', text).strip()
    has_timeline = 'Timeline' in b or 'timeline' in b
    has_futures = 'Futures' in b or 'futures' in b
    has_q1 = 'Q1' in b
    print(f"Block {i} ({len(b)} chars) timeline:{has_timeline} futures:{has_futures} Q1:{has_q1}")
    print(f"  Text: {text[:200]}")
    print()
