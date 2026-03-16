"""Find Apps As Peers images in the media library and check production site."""
import requests, re

AZURE = "https://azure-nightingale-589250.hostingersite.com"
PROD = "https://polysaas.online"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Search Azure media library
for term in ["apps as peers", "apps-as-peers", "peers"]:
    r = s.get(f"{AZURE}/wp-json/wp/v2/media", params={"per_page": 100, "search": term})
    media = r.json()
    if media:
        print(f"Azure media matching '{term}': {len(media)}")
        for m in media:
            print(f"  id={m['id']}  title={m['title']['rendered']}")
            print(f"    url={m['source_url']}")

# Check production Apps As Peers page for images
print("\n=== Checking production site ===")
r2 = requests.get(f"{PROD}/apps-as-peers/", timeout=15)
if r2.status_code == 200:
    imgs = re.findall(r'<img[^>]+src="([^"]+)"[^>]*>', r2.text)
    print(f"Found {len(imgs)} images on production Apps As Peers page")
    for img in imgs:
        alt = ""
        match = re.search(r'<img[^>]+src="' + re.escape(img) + r'"[^>]*alt="([^"]*)"', r2.text)
        if match:
            alt = match.group(1)
        if 'logo' not in img.lower() and 'favicon' not in img.lower() and 'gravatar' not in img.lower():
            print(f"  {img}")
            if alt:
                print(f"    alt: {alt}")
else:
    print(f"Production page: {r2.status_code}")

# Also try wp-json on production
try:
    r3 = requests.get(f"{PROD}/wp-json/wp/v2/pages?slug=apps-as-peers", timeout=15)
    if r3.status_code == 200:
        pages = r3.json()
        if pages:
            content = pages[0].get('content', {}).get('rendered', '')
            imgs2 = re.findall(r'<img[^>]+src="([^"]+)"[^>]*>', content)
            print(f"\nProduction API: {len(imgs2)} images in content")
            for img in imgs2:
                print(f"  {img}")
except Exception as e:
    print(f"Production API error: {e}")
