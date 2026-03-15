"""
Audit all application and feature detail pages on polysaas.online
to identify meaningful content and images for migration to Azure.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROD = "https://polysaas.online"

APP_PAGES = [
    'odoo', 'nextcloud', 'mattermost', 'monitor-logger',
    'liferay', 'polysysmon', 'dolibarr', 'wordpress'
]

FEATURE_PAGES = [
    'architecture', 'portal', 'atomic-services', 'dynamic-orchestration',
    'openapi', 'apps-as-peers', 'ai-as-peers', 'bundled-applications'
]

ALL_PAGES = APP_PAGES + FEATURE_PAGES

for slug in ALL_PAGES:
    try:
        r = requests.get(f"{PROD}/{slug}/", timeout=15)
        if r.status_code != 200:
            print(f"\n{'='*60}")
            print(f"  {slug}: HTTP {r.status_code}")
            continue
        
        html = r.text
        
        # Extract images (skip tiny icons, favicons, etc)
        imgs = re.findall(r'<img[^>]*src="([^"]*)"[^>]*>', html)
        # Filter out tiny/utility images
        meaningful_imgs = []
        for img in imgs:
            if any(skip in img.lower() for skip in ['favicon', 'logo-icon', '1x1', 'pixel', 'gravatar', 'wp-includes']):
                continue
            meaningful_imgs.append(img)
        
        # Extract text content (strip scripts, styles, nav, footer)
        # Remove header/nav
        body = html
        main_match = re.search(r'<main[^>]*>(.*?)</main>', body, re.DOTALL)
        if main_match:
            body = main_match.group(1)
        else:
            # Try entry-content
            content_match = re.search(r'class="entry-content[^"]*"[^>]*>(.*?)</article>', body, re.DOTALL)
            if content_match:
                body = content_match.group(1)
        
        # Strip scripts and styles
        body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
        body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
        
        # Extract headings
        headings = re.findall(r'<h[1-4][^>]*>(.*?)</h[1-4]>', body, re.DOTALL)
        headings = [re.sub(r'<[^>]+>', '', h).strip() for h in headings]
        
        # Extract paragraphs
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', body, re.DOTALL)
        paragraphs = [re.sub(r'<[^>]+>', '', p).strip() for p in paragraphs if len(re.sub(r'<[^>]+>', '', p).strip()) > 30]
        
        # Get total text length
        text = re.sub(r'<[^>]+>', ' ', body)
        text = re.sub(r'\s+', ' ', text).strip()
        
        print(f"\n{'='*60}")
        print(f"  {slug}")
        print(f"{'='*60}")
        print(f"  Text: {len(text)} chars")
        print(f"  Headings ({len(headings)}):")
        for h in headings[:8]:
            print(f"    - {h[:80]}")
        print(f"  Paragraphs: {len(paragraphs)}")
        for p in paragraphs[:3]:
            print(f"    > {p[:120]}...")
        print(f"  Images ({len(meaningful_imgs)}):")
        for img in meaningful_imgs:
            # Get just filename
            fname = img.split('/')[-1].split('?')[0]
            print(f"    - {fname}")
            print(f"      {img[:120]}")
            
    except Exception as e:
        print(f"\n  {slug}: ERROR - {e}")
