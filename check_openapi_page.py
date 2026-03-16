"""Check current OpenAPI/Swagger page content and compare with a good detail page."""
import requests, re

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get OpenAPI page
r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=openapi-2&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']
title = page['title']['raw']
print(f"OpenAPI page: id={pid}, title={title}")
print(f"Content length: {len(content)}")

# Show content after style blocks
toggle_idx = content.find('ps-dark-toggle')
if toggle_idx >= 0:
    wp_close = content.find('<!-- /wp:html -->', toggle_idx)
    if wp_close >= 0:
        after = content[wp_close:]
        print(f"\n=== CONTENT AFTER TOGGLE ({len(after)} chars) ===")
        print(after[:3000])
        print("=== END ===")

# Also get a good reference page for format comparison
r2 = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=odoo&context=edit")
odoo = r2.json()[0]
odoo_content = odoo['content']['raw']
toggle_idx2 = odoo_content.find('ps-dark-toggle')
wp_close2 = odoo_content.find('<!-- /wp:html -->', toggle_idx2)
after_odoo = odoo_content[wp_close2:]
print(f"\n=== ODOO REFERENCE FORMAT (first 2000 chars after toggle) ===")
print(after_odoo[:2000])
print("=== END ===")

# Check for existing images
imgs = re.findall(r'<img[^>]+src="([^"]+)"[^>]*>', content)
print(f"\nOpenAPI images: {len(imgs)}")
for img in imgs:
    print(f"  {img}")
