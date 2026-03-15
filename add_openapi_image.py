"""
Add Swagger UI screenshot to the OpenAPI detail page.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

SWAGGER_URL = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/02/swagger-ui-1-scaled.png"

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "openapi-2", "context": "edit", "_fields": "id,content"
}).json()
if not pages:
    pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
        "per_page": 100, "context": "edit", "_fields": "id,slug,content"
    }).json()
    pages = [p for p in pages if 'openapi' in p['slug']]

page = pages[0]
raw = page['content']['raw']
print(f"OpenAPI page: slug={page.get('slug', 'openapi-2')}, {len(raw)} chars")

# Check if image already present
if 'swagger-ui' in raw:
    print("Swagger UI image already on page!")
else:
    img_block = f'''<div style="text-align:center;margin:20px auto;">
<img src="{SWAGGER_URL}" alt="PolySaaS OpenAPI Swagger UI" style="width:100%;max-width:800px;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="color:var(--ps-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">PolySaaS OpenAPI documentation via Swagger UI — explore and test all API endpoints interactively</p>
</div>'''

    # Find insertion point before Key Capabilities
    key_cap_idx = raw.find('Key Capabilities')
    if key_cap_idx < 0:
        key_cap_idx = raw.find('Key Features')
    
    if key_cap_idx > 0:
        insert_before = raw.rfind('<h2', max(0, key_cap_idx - 100), key_cap_idx)
        if insert_before < 0:
            insert_before = key_cap_idx
        new_raw = raw[:insert_before] + img_block + "\n" + raw[insert_before:]
    else:
        # Fallback: after subtitle
        subtitle_end = raw.find('</p>', raw.find('font-weight:500'))
        if subtitle_end > 0:
            insert_after = subtitle_end + 4
            new_raw = raw[:insert_after] + "\n" + img_block + "\n" + raw[insert_after:]
        else:
            print("Could not find insertion point")
            sys.exit(1)
    
    r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page['id']}", json={"content": new_raw})
    print(f"Update: {r.status_code}")
    if r.status_code == 200:
        print("Swagger UI screenshot added to OpenAPI page")
