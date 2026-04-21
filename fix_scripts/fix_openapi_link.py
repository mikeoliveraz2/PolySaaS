"""Check /openapi/ vs /openapi-2/ and fix the link."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Check what's at /openapi/
r1 = requests.get(BASE + "/openapi/", timeout=30)
print(f"/openapi/ status: {r1.status_code}, length: {len(r1.text)}")
if r1.status_code == 200:
    html = r1.text
    # Check content
    for check in ['Standardized API', 'Key Capabilities', 'swagger-ui']:
        print(f"  {'FOUND' if check in html else 'MISSING'}: {check}")
    # Look for what IS on the page
    title = re.search(r'<title>(.*?)</title>', html)
    print(f"  Title: {title.group(1) if title else 'N/A'}")
    # Find main content
    entry = re.search(r'entry-content-wrap.*?</article>', html, re.DOTALL)
    if entry:
        content_area = entry.group(0)
        headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', content_area)
        imgs = re.findall(r'<img[^>]+src="([^"]+)"', content_area)
        paras = re.findall(r'<p[^>]*>([^<]+)</p>', content_area)
        print(f"  Headings: {[re.sub(r'<[^>]+>', '', h).strip() for h in headings[:5]]}")
        print(f"  Images: {len(imgs)}")
        for i in imgs[:3]:
            print(f"    {i[:100]}")
        print(f"  Paragraphs: {len(paras)}")

# Find the /openapi/ page in WordPress
r2 = requests.get(BASE + "/wp-json/wp/v2/pages",
                  params={"slug": "openapi", "_fields": "id,title,slug,status,content", "context": "edit"},
                  auth=AUTH, timeout=30)
openapi_pages = r2.json()
print(f"\n=== Pages with slug 'openapi' ===")
for p in openapi_pages:
    print(f"  ID {p['id']}: {p['title']['raw']} (slug: {p['slug']})")
    c = p['content']['raw']
    print(f"  Content length: {len(c)} chars")
    print(f"  Content preview: {c[:500]}")
