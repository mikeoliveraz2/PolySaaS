"""List the first 10 images in DOM order from the gallery grid."""
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

gallery_start = raw.find('columns:2;column-gap')
if gallery_start < 0:
    print("Gallery grid not found")
    sys.exit(1)

gallery_end = raw.find('</div>\n<!-- /wp:html -->', gallery_start)
gallery_html = raw[gallery_start:gallery_end]

items = re.findall(
    r'<div style="break-inside:avoid.*?<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)".*?</div>',
    gallery_html, re.DOTALL
)

print(f"First 10 images in gallery (DOM order):")
print("In CSS columns:2, these fill LEFT column top-to-bottom first\n")
for i, (url, alt) in enumerate(items[:10], 1):
    fn = url.split('/')[-1]
    print(f"  {i}. [{alt}] -> {fn}")
