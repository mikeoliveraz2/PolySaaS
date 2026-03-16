"""Rebuild the OpenAPI/Swagger page with proper content matching other detail pages."""
import requests, re

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get Odoo as reference for preamble format
r_ref = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=odoo&context=edit")
odoo = r_ref.json()[0]
odoo_content = odoo['content']['raw']

# Find the Odoo title
idx = odoo_content.find('>Odoo</h2>')
if idx < 0:
    print("Cannot find Odoo title, searching...")
    for term in ['Odoo', 'ODOO']:
        idx = odoo_content.find(f'>{term}</h2>')
        if idx >= 0:
            break

if idx >= 0:
    # Find the <!-- /wp:html --> after it
    wp_close = odoo_content.find('<!-- /wp:html -->', idx)
    if wp_close >= 0:
        preamble_end = wp_close + len('<!-- /wp:html -->')
    else:
        preamble_end = idx + len('>Odoo</h2>')
    
    preamble = odoo_content[:preamble_end]
    preamble = preamble.replace('>Odoo</h2>', '>OpenAPI / Swagger</h2>')
    print(f"Preamble: {len(preamble)} chars")
else:
    # Fallback: get the OpenAPI page and extract just the CSS/toggle
    print("Odoo title not found, using OpenAPI page preamble")
    r_oapi = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=openapi-2&context=edit")
    oapi = r_oapi.json()[0]
    oapi_content = oapi['content']['raw']
    
    # Find the toggle, then look for the title
    toggle_idx = oapi_content.find('ps-dark-toggle')
    if toggle_idx >= 0:
        wp_close = oapi_content.find('<!-- /wp:html -->', toggle_idx)
        preamble = oapi_content[:wp_close + len('<!-- /wp:html -->')]
        # Add the title
        preamble += '\n<!-- wp:html -->\n<h2 style="text-align:center;padding:5px 0 0 0;margin:0;color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;">OpenAPI / Swagger</h2>\n<!-- /wp:html -->'
    else:
        preamble = '<!-- wp:html -->\n<h2 style="text-align:center;padding:5px 0 0 0;margin:0;color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;">OpenAPI / Swagger</h2>\n<!-- /wp:html -->'
    print(f"Fallback preamble: {len(preamble)} chars")

# Image URLs
swagger_ui = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/swagger-ui-dose-api.png"
swagger_endpoints = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/swagger-api-endpoints.png"

body = """
<!-- wp:html -->
<p style="text-align:center;color:var(--ps-accent,#0F766E);font-size:1.2rem;margin:0 0 20px 0;font-weight:500;">Standardized API Documentation</p>

<p style="font-size:1.1rem;line-height:1.8;max-width:800px;margin:0 auto 20px;text-align:center;">Every Atomic Service and integration endpoint in PolySaaS is documented with OpenAPI (Swagger) specifications. Explore, test, and integrate with any external system using standard Swagger interfaces — making PolySaaS fully programmable and transparently documented.</p>

<div style="text-align:center;margin:20px auto;">
<img src="{swagger_ui}" alt="Swagger UI — PolySaaS DOSE API" style="width:100%;max-width:900px;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="font-size:0.9rem;color:#666;margin-top:8px;font-style:italic;">Swagger UI — interactive API documentation for the PolySaaS DOSE API</p>
</div>

<div style="text-align:center;margin:20px auto;">
<img src="{swagger_endpoints}" alt="API Endpoints — Atomic Services CRUD operations" style="width:100%;max-width:900px;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="font-size:0.9rem;color:#666;margin-top:8px;font-style:italic;">API endpoints — full CRUD operations for Atomic Services and callback data</p>
</div>
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
""".format(swagger_ui=swagger_ui, swagger_endpoints=swagger_endpoints)

new_content = preamble + '\n' + body
print(f"Final content: {len(new_content)} chars")

# Update
r_page = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=openapi-2&context=edit")
pid = r_page.json()[0]['id']

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("Done — OpenAPI/Swagger page rebuilt with Swagger screenshots and full detail content.")
else:
    print(f"Error: {r2.text[:500]}")
