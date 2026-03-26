"""Check the OpenAPI/Swagger page content."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Find the OpenAPI page
r = requests.get(f"{BASE}/wp-json/wp/v2/pages?search=OpenAPI&_fields=id,title,slug,status&context=edit",
                 auth=AUTH, timeout=15)
pages = r.json()
print("=== OpenAPI pages ===")
for p in pages:
    print(f"  ID {p['id']}: {p['title']['raw']} (slug: {p['slug']}, status: {p['status']})")

# Get the page content
if pages:
    page_id = pages[0]['id']
    r2 = requests.get(f"{BASE}/wp-json/wp/v2/pages/{page_id}?context=edit&_fields=content",
                      auth=AUTH, timeout=15)
    content = r2.json()['content']['raw']
    print(f"\n=== Page {page_id} content ({len(content)} chars) ===")
    print(content[:3000])
    if len(content) > 3000:
        print(f"\n... ({len(content) - 3000} more chars)")

# Also check what the rendered page looks like
r3 = requests.get(f"{BASE}/openapi-swagger/", timeout=15)
print(f"\n=== Rendered page status: {r3.status_code} ===")
if r3.status_code == 200:
    html = r3.text
    # Find the main content area
    import re
    entry = re.search(r'entry-content-wrap.*?</article>', html, re.DOTALL)
    if entry:
        content_area = entry.group(0)
        print(f"Content area length: {len(content_area)}")
        # Check for images, text, headings
        imgs = re.findall(r'<img[^>]+src="([^"]+)"', content_area)
        headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', content_area)
        paras = re.findall(r'<p[^>]*>(.*?)</p>', content_area, re.DOTALL)
        print(f"Images: {len(imgs)}")
        for img in imgs:
            print(f"  {img[:100]}")
        print(f"Headings: {headings[:5]}")
        print(f"Paragraphs: {len(paras)}")
        for p in paras[:3]:
            clean = re.sub(r'<[^>]+>', '', p).strip()
            if clean:
                print(f"  {clean[:150]}")
