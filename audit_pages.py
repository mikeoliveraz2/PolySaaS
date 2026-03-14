"""Audit all application and feature pages to see what content they have"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,title,content"
})
pages = r.json()

# The 8 bundled app pages
APP_SLUGS = ['odoo', 'nextcloud', 'mattermost', 'wordpress-3', 'liferay-2', 'dolibarr-3', 'monitor-logger-4', 'polysysmon']
# The feature pages
FEATURE_SLUGS = ['architecture', 'portal', 'dynamic-orchestration', 'polysniffer', 'apps-as-peers', 'openapi-2', 'ai-as-peers', 'bundled-applications']

TARGET_SLUGS = APP_SLUGS + FEATURE_SLUGS

for page in sorted(pages, key=lambda p: p['slug']):
    slug = page['slug']
    if slug not in TARGET_SLUGS:
        continue
    
    title = page['title']['raw'] if isinstance(page['title'], dict) else page['title']
    raw = page['content']['raw']
    
    # Strip CSS/toggle blocks to get actual content
    content_only = re.sub(r'<!-- wp:html -->.*?<!-- /wp:html -->', '', raw, flags=re.DOTALL)
    content_only = re.sub(r'<style>.*?</style>', '', content_only, flags=re.DOTALL)
    content_only = re.sub(r'<[^>]+>', '', content_only)  # strip HTML tags
    content_only = content_only.strip()
    
    # Count headings in raw
    headings = re.findall(r'<h[1-4][^>]*>([^<]+)</h', raw)
    
    # Check for images
    images = re.findall(r'<img[^>]*src="([^"]+)"', raw)
    content_images = [i for i in images if 'Industrial-PolySaas' not in i]  # exclude logo
    
    content_len = len(content_only)
    category = "APP" if slug in APP_SLUGS else "FEATURE"
    
    print(f"\n[{category}] {slug} - \"{title}\"")
    print(f"  Content length: {content_len} chars")
    print(f"  Headings: {len(headings)} - {headings[:5]}")
    print(f"  Images: {len(content_images)}")
    if content_len < 200:
        print(f"  TEXT: {content_only[:200]}")
    else:
        print(f"  TEXT preview: {content_only[:150]}...")
