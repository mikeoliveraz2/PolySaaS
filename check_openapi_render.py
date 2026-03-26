"""Check if OpenAPI page images exist and verify the Learn More link."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"

# Check the two screenshots referenced in the page
images = [
    "/wp-content/uploads/2026/03/swagger-ui-dose-api.png",
    "/wp-content/uploads/2026/03/swagger-api-endpoints.png",
]
print("=== Image checks ===")
for img in images:
    r = requests.head(BASE + img, timeout=15, allow_redirects=True)
    print(f"  {r.status_code}: {img}")

# Check what the homepage Learn More link points to for OpenAPI
r2 = requests.get(BASE, timeout=30)
html = r2.text

# Find OpenAPI section and its Learn More link
import re
# Find the OpenAPI heading and nearby Learn More link
openapi_pos = html.find('OpenAPI / Swagger')
if openapi_pos > 0:
    # Get a chunk after the heading
    chunk = html[openapi_pos:openapi_pos+1000]
    links = re.findall(r'href="([^"]*)"', chunk)
    print(f"\n=== Links near OpenAPI heading ===")
    for link in links[:5]:
        print(f"  {link}")

# Check the rendered OpenAPI page
r3 = requests.get(BASE + "/openapi-2/", timeout=30)
print(f"\n=== Rendered OpenAPI page: {r3.status_code} ===")
if r3.status_code == 200:
    rhtml = r3.text
    print(f"Page length: {len(rhtml)}")
    # Check for key content
    for check in ['Standardized API Documentation', 'Key Capabilities', 'swagger-ui', 'Interactive API Explorer']:
        print(f"  {'FOUND' if check in rhtml else 'MISSING'}: {check}")
elif r3.status_code == 404:
    print("  PAGE NOT FOUND!")
    # Try other possible slugs
    for slug in ['openapi', 'openapi-swagger', 'open-api']:
        r4 = requests.get(BASE + f"/{slug}/", timeout=15)
        print(f"  Trying /{slug}/: {r4.status_code}")
