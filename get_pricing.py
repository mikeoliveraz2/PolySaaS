"""
Get pricing content from polysaas.online and check current Azure pricing page.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Check production site pricing page
PROD = "https://polysaas.online"
AZURE = "https://azure-nightingale-589250.hostingersite.com"

# Try to get pricing from production site
s_prod = requests.Session()
try:
    r = s_prod.get(f"{PROD}/pricing/", timeout=15)
    print(f"Production pricing page: {r.status_code}")
    if r.status_code == 200:
        html = r.text
        # Extract text content from the pricing section
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '\n', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        # Find pricing-related content
        lines = text.split('\n')
        in_pricing = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if any(kw in line.lower() for kw in ['pricing', 'starter', 'team', 'unlimited', 'enterprise', '$', 'month', '/mo', 'plan', 'tier']):
                in_pricing = True
            if in_pricing and line:
                print(f"  {line}")
except Exception as e:
    print(f"Production error: {e}")

# Also try the WP REST API on production
print("\n--- Production REST API ---")
try:
    r2 = s_prod.get(f"{PROD}/wp-json/wp/v2/pages", params={
        "per_page": 100, "_fields": "id,slug,title,content"
    }, timeout=15)
    if r2.status_code == 200:
        for p in r2.json():
            slug = p['slug']
            if 'pric' in slug.lower():
                title = p['title']['rendered'] if isinstance(p['title'], dict) else p['title']
                content = p['content']['rendered'] if isinstance(p['content'], dict) else p['content']
                text = re.sub(r'<[^>]+>', ' ', content)
                text = re.sub(r'\s+', ' ', text).strip()
                print(f"Page: {slug} - {title}")
                print(f"  Content ({len(text)} chars): {text[:1000]}")
    else:
        print(f"  API returned {r2.status_code}")
except Exception as e:
    print(f"  API error: {e}")

# Check current Azure pricing page
print("\n--- Azure Pricing Page ---")
s_az = requests.Session()
s_az.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")
r3 = s_az.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content,title"
})
for p in r3.json():
    if 'pric' in p['slug'].lower():
        title = p['title']['raw'] if isinstance(p['title'], dict) else p['title']
        raw = p['content']['raw']
        text = re.sub(r'<[^>]+>', ' ', raw)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        text = re.sub(r'\{[^}]+\}', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        print(f"Page: {p['slug']} (id={p['id']}) - {title}")
        print(f"  Raw: {len(raw)} chars")
        print(f"  Text: {text[:500]}")
