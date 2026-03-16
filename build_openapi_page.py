"""Upload Swagger screenshot and build full OpenAPI/Swagger detail page."""
import requests, re

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Upload the Swagger UI screenshot
filepath = r"c:\Users\PC\AppData\Local\Temp\cursor\screenshots\page-2026-03-15T02-10-24-663Z.png"
print("Uploading Swagger UI screenshot...")
with open(filepath, "rb") as f:
    data = f.read()

r_up = s.post(f"{AZURE}/wp-json/wp/v2/media",
    headers={
        "Content-Disposition": 'attachment; filename="swagger-ui-dose-api.png"',
        "Content-Type": "image/png"
    },
    data=data)

if r_up.status_code == 201:
    swagger_url = r_up.json()["source_url"]
    swagger_id = r_up.json()["id"]
    print(f"Uploaded: id={swagger_id} url={swagger_url}")
else:
    print(f"Upload failed: {r_up.status_code}, checking existing...")
    r_check = s.get(f"{AZURE}/wp-json/wp/v2/media", params={"search": "swagger-ui-dose"})
    existing = r_check.json()
    if existing:
        swagger_url = existing[0]["source_url"]
        swagger_id = existing[0]["id"]
        print(f"Using existing: id={swagger_id}")
    else:
        print("No existing found either, abort")
        exit(1)

# Upload the endpoints screenshot too
filepath2 = r"c:\Users\PC\AppData\Local\Temp\cursor\screenshots\page-2026-03-15T02-10-45-580Z.png"
print("Uploading API endpoints screenshot...")
with open(filepath2, "rb") as f:
    data2 = f.read()

r_up2 = s.post(f"{AZURE}/wp-json/wp/v2/media",
    headers={
        "Content-Disposition": 'attachment; filename="swagger-api-endpoints.png"',
        "Content-Type": "image/png"
    },
    data=data2)

if r_up2.status_code == 201:
    endpoints_url = r_up2.json()["source_url"]
    endpoints_id = r_up2.json()["id"]
    print(f"Uploaded: id={endpoints_id} url={endpoints_url}")
else:
    print(f"Endpoints upload: {r_up2.status_code}")
    endpoints_url = None

# Also get the existing Swagger screenshot already in the library
existing_swagger = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/02/swagger-ui-1-scaled.png"

# Get the OpenAPI page
r_page = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=openapi-2&context=edit")
page = r_page.json()[0]
pid = page['id']
old_content = page['content']['raw']
print(f"\nOpenAPI page id={pid}, old content length={len(old_content)}")

# Extract the CSS/style blocks and toggle from the existing content
# Find everything up to and including the title H2
title_match = re.search(r'<!-- wp:html -->\s*<h2[^>]*>OpenAPI / Swagger</h2>\s*<!-- /wp:html -->', old_content)
if title_match:
    preamble = old_content[:title_match.end()]
    print(f"Found title block, preamble length={len(preamble)}")
else:
    # Find the last style/toggle section
    toggle_end = old_content.find('ps-dark-toggle')
    if toggle_end >= 0:
        wp_close = old_content.find('<!-- /wp:html -->', toggle_end)
        # Then find the title
        title_h2 = old_content.find('>OpenAPI / Swagger</h2>', wp_close)
        if title_h2 >= 0:
            end_of_title = old_content.find('<!-- /wp:html -->', title_h2)
            preamble = old_content[:end_of_title + len('<!-- /wp:html -->')]
        else:
            preamble = old_content[:wp_close + len('<!-- /wp:html -->')]
    else:
        preamble = old_content[:1000]
    print(f"Preamble length={len(preamble)}")

# Build the new page content (same format as other detail pages)
new_body = '''
<!-- wp:html -->
<h2 class="wp-block-heading has-text-align-center" style="color:#0F766E !important;font-size:1.4rem;font-weight:600;margin-bottom:12px;">Standardized API Documentation</h2>

<p class="has-text-align-center" style="font-size:1.1rem;line-height:1.8;max-width:800px;margin:0 auto 20px;">Every Atomic Service and integration endpoint in PolySaaS is documented with OpenAPI (Swagger) specifications. Explore, test, and integrate with any external system using standard Swagger interfaces — making PolySaaS fully programmable and transparently documented.</p>

<div style="text-align:center;margin:20px auto;">
<img src="{swagger_url}" alt="Swagger UI — PolySaaS DOSE API" style="width:100%;max-width:900px;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="font-size:0.9rem;color:#666;margin-top:8px;font-style:italic;">Swagger UI — interactive API documentation for the PolySaaS DOSE API</p>
</div>

{endpoints_block}

<!-- /wp:html -->

<h2 class="wp-block-heading" style="font-size:1.8rem;font-weight:700;margin:30px 0 15px;">Key Capabilities</h2>

<!-- wp:html -->
<div style="background:var(--ps-bg-alt,#F3F4F6);border-radius:12px;padding:24px 28px;margin-bottom:16px;border-left:4px solid var(--ps-accent,#0F766E);">
<h3 style="font-size:1.2rem;font-weight:700;margin:0 0 8px;">Interactive API Explorer</h3>
<p style="margin:0;line-height:1.7;">Browse every endpoint with full request/response schemas. Try API calls directly from the Swagger UI — no external tools needed. See exactly what data each service accepts and returns.</p>
</div>

<div style="background:var(--ps-bg-alt,#F3F4F6);border-radius:12px;padding:24px 28px;margin-bottom:16px;border-left:4px solid var(--ps-accent,#0F766E);">
<h3 style="font-size:1.2rem;font-weight:700;margin:0 0 8px;">Full CRUD Operations</h3>
<p style="margin:0;line-height:1.7;">Every resource supports standard REST operations — GET, POST, PUT, PATCH, DELETE — with consistent URL patterns and response formats across all services.</p>
</div>

<div style="background:var(--ps-bg-alt,#F3F4F6);border-radius:12px;padding:24px 28px;margin-bottom:16px;border-left:4px solid var(--ps-accent,#0F766E);">
<h3 style="font-size:1.2rem;font-weight:700;margin:0 0 8px;">Atomic Services API</h3>
<p style="margin:0;line-height:1.7;">Create, configure, and manage Atomic Services programmatically. Define workflow triggers, data transformations, and inter-application actions through documented endpoints.</p>
</div>

<div style="background:var(--ps-bg-alt,#F3F4F6);border-radius:12px;padding:24px 28px;margin-bottom:16px;border-left:4px solid var(--ps-accent,#0F766E);">
<h3 style="font-size:1.2rem;font-weight:700;margin:0 0 8px;">Authentication & Security</h3>
<p style="margin:0;line-height:1.7;">OAuth2 and token-based authentication documented inline. Django Login integration for session-based access. Every endpoint clearly shows its authentication requirements.</p>
</div>

<div style="background:var(--ps-bg-alt,#F3F4F6);border-radius:12px;padding:24px 28px;margin-bottom:16px;border-left:4px solid var(--ps-accent,#0F766E);">
<h3 style="font-size:1.2rem;font-weight:700;margin:0 0 8px;">PolySaaS Integration</h3>
<p style="margin:0;line-height:1.7;">OpenAPI specifications power the entire PolySaaS integration layer. External systems connect through documented APIs, Dynamic Orchestration uses endpoint schemas for validation, and every Atomic Service is automatically registered in the Swagger catalog — ensuring your platform is always fully documented and accessible.</p>
</div>

<!-- /wp:html -->

<!-- wp:html -->
<div style="text-align:center;margin:40px auto 20px;padding:30px 20px;background:linear-gradient(135deg, var(--ps-bg-alt,#F3F4F6) 0%, var(--ps-bg,#FFFFFF) 100%);border-radius:16px;">
<h3 style="font-size:1.3rem;font-weight:700;color:var(--ps-primary,#001F3F) !important;margin-bottom:8px;">Stop Managing Tools. Start Orchestrating Them.</h3>
<p style="color:var(--ps-text-muted,#4B5563);margin-bottom:16px;">Join enterprises already running smarter with PolySaaS.</p>
<a href="/schedule-demo/" style="display:inline-block;padding:12px 28px;background:var(--ps-primary,#001F3F);color:#FFFFFF !important;text-decoration:none;border-radius:8px;font-weight:600;font-size:1rem;">Sign Up for a Demo</a>
</div>
<!-- /wp:html -->
'''.format(
    swagger_url=swagger_url,
    endpoints_block=f'''<div style="text-align:center;margin:20px auto;">
<img src="{endpoints_url}" alt="API Endpoints — Atomic Services CRUD operations" style="width:100%;max-width:900px;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="font-size:0.9rem;color:#666;margin-top:8px;font-style:italic;">API endpoints showing full CRUD operations for Atomic Services and callback data</p>
</div>''' if endpoints_url else ''
)

new_content = preamble + new_body
print(f"New content length: {len(new_content)}")

r_update = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Update: {r_update.status_code}")
if r_update.status_code == 200:
    print("Done — OpenAPI/Swagger detail page rebuilt.")
else:
    print(f"Error: {r_update.text[:500]}")
