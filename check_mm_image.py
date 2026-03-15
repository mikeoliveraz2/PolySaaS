"""
Check if the Business Plan chat image is accessible and verify the URL in the page.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Check the image URL directly
IMG_URL = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/Business-Plan-PolySaaS-Mattermost-03-06-2026_02_23_PM-scaled.png"
r = requests.head(IMG_URL, timeout=10)
print(f"Image URL status: {r.status_code}")
print(f"Content-Type: {r.headers.get('Content-Type')}")
print(f"Content-Length: {r.headers.get('Content-Length')}")

# Also check what sizes are available
media = s.get(f"{AZURE}/wp-json/wp/v2/media/1730", params={"_fields": "id,source_url,media_details"}).json()
print(f"\nMedia 1730 source: {media.get('source_url')}")
if 'media_details' in media:
    details = media['media_details']
    print(f"Width: {details.get('width')}, Height: {details.get('height')}")
    if 'sizes' in details:
        for name, info in details['sizes'].items():
            print(f"  Size '{name}': {info.get('width')}x{info.get('height')} - {info.get('source_url','')[:100]}")

# Check the actual HTML on the page
pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "mattermost", "context": "edit", "_fields": "id,content"
}).json()
raw = pages[0]['content']['raw']
biz_idx = raw.find('Business Plan Group Chat')
if biz_idx > 0:
    print(f"\nBusiness Plan section:")
    print(raw[biz_idx:biz_idx+600])
