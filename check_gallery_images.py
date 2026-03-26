import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages",
          params={"slug": "gallery-images", "context": "edit", "_fields": "id,content"},
          timeout=30)
page = r.json()[0]
raw = page['content']['raw']
print(f"Page ID: {page['id']}, length: {len(raw)} chars")

# Find all images and their alt text
imgs = re.findall(r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"', raw)
print(f"\n{len(imgs)} images found:")
for i, (url, alt) in enumerate(imgs, 1):
    filename = url.split('/')[-1]
    topflite = " <-- TOPFLITE" if 'topflite' in url.lower() or 'topflite' in alt.lower() or 'top-flite' in url.lower() or 'top_flite' in url.lower() else ""
    print(f"  {i:2d}. {alt:50s} {filename}{topflite}")
