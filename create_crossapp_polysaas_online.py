"""
Create the Cross-App Sync page on polysaas.online (PRODUCTION).
Uploads all screenshots, creates the page, and links from Dynamic Orchestration and PolySniffer pages.
"""
import requests, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")
s = requests.Session()
s.auth = AUTH

UPLOADS = r"D:\PolySaaS\dose\website\staging\wp-content\uploads"
ASSETS = r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets"

# ============================================================
# STEP 1: Upload all images
# ============================================================

IMAGES = [
    {"file": os.path.join(UPLOADS, "PolySniffer-Live-Capture-Dolibarr-ERP-03-22-2026_10_41_AM.png"),
     "wp_name": "crossapp-polysniffer-dolibarr-capture.png",
     "alt": "PolySniffer live capture dashboard showing Dolibarr HTTP traffic",
     "caption": "PolySniffer captures all HTTP traffic between the browser and Dolibarr ERP"},
    {"file": os.path.join(UPLOADS, "Select-pass-through-endpoint-to-change-D-O-S-E-Administration-03-22-2026_10_44_AM.png"),
     "wp_name": "crossapp-passthrough-endpoints-admin.png",
     "alt": "Django admin showing PassThrough endpoints with PolySniffer Analysis buttons",
     "caption": "PassThrough endpoint configuration with PolySniffer Analysis for Dolibarr ERP"},
    {"file": os.path.join(UPLOADS, "Login-19-0-2-03-22-2026_10_43_AM.png"),
     "wp_name": "crossapp-dolibarr-login.png",
     "alt": "Dolibarr 19.0.2 login screen accessed through PolySniffer proxy",
     "caption": "Dolibarr 19.0.2 login page -- all traffic captured by PolySniffer"},
    {"file": os.path.join(UPLOADS, "Setup-03-22-2026_10_43_AM.png"),
     "wp_name": "crossapp-dolibarr-setup-thirdparties.png",
     "alt": "Dolibarr admin dashboard with Third-parties menu highlighted",
     "caption": "Navigating to Third-parties module"},
    {"file": os.path.join(UPLOADS, "Third-parties-03-22-2026_10_43_AM.png"),
     "wp_name": "crossapp-dolibarr-thirdparties-menu.png",
     "alt": "Dolibarr Third-parties sidebar showing New Customer option",
     "caption": "Third-parties sidebar: New Customer selected"},
    {"file": os.path.join(UPLOADS, "New-Third-Party-prospect-customer-vendor--03-22-2026_10_42_AM.png"),
     "wp_name": "crossapp-dolibarr-new-thirdparty-form.png",
     "alt": "Dolibarr New Third Party form filled with customer data",
     "caption": "New Third Party form: name, address, phone, and customer classification fields"},
    {"file": os.path.join(UPLOADS, "Annotate-Image-03-22-2026_10_42_AM.png"),
     "wp_name": "crossapp-dolibarr-create-thirdparty-submit.png",
     "alt": "Dolibarr Create Third Party form bottom section with submit button",
     "caption": "Bottom of the form: Professional IDs, sales tax, third-party type, and CREATE button"},
    {"file": os.path.join(UPLOADS, "Mike-Oliver-Card-03-22-2026_10_41_AM.png"),
     "wp_name": "crossapp-dolibarr-customer-created.png",
     "alt": "Dolibarr customer record for Mike Oliver showing synced data",
     "caption": "Customer created: Mike Oliver with code CU2603-00001"},
    {"file": os.path.join(UPLOADS, "Odoo-Contacts-Mike-Oliver-Grid-03-22-2026.png"),
     "wp_name": "crossapp-odoo-contacts-grid-mike-oliver.png",
     "alt": "Odoo Contacts grid view showing Mike Oliver synced from Dolibarr",
     "caption": "Mike Oliver appears in Odoo Contacts -- synced automatically from Dolibarr via RabbitMQ"},
    {"file": os.path.join(UPLOADS, "Odoo-Contact-Mike-Oliver-Detail-03-22-2026.png"),
     "wp_name": "crossapp-odoo-contact-mike-oliver-detail.png",
     "alt": "Odoo Contact detail page for Mike Oliver showing all synced fields",
     "caption": "Full Odoo record: name, address, phone, mobile, email -- all mapped from the Dolibarr form POST"},
    {"file": os.path.join(ASSETS, "c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_image-5f6b435e-389d-4dd5-8645-06f5ebd5a779.png"),
     "wp_name": "crossapp-instruction-list-olient.png",
     "alt": "Django admin Instructions list in olient tenant showing cross-app sync entries",
     "caption": "Instructions list in Oliver Enterprises tenant"},
    {"file": os.path.join(ASSETS, "c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_image-4433a229-7f52-4de7-bef8-d409f2adfee1.png"),
     "wp_name": "crossapp-instruction-detail-dolibarr.png",
     "alt": "Django admin Instruction detail for Dolibarr POST capture",
     "caption": "Instruction detail: /societe/card.php POST with eventKey dolibarr.customer.created"},
]

uploaded_urls = {}
print("=== Uploading images to polysaas.online ===\n")

for img in IMAGES:
    if not os.path.exists(img["file"]):
        print(f"  SKIP: {img['wp_name']} - file not found at {img['file']}")
        continue

    with open(img["file"], "rb") as f:
        data = f.read()

    print(f"  {img['wp_name']} ({len(data)//1024}KB)...", end=" ")

    r = s.post(BASE + "/wp-json/wp/v2/media",
        headers={"Content-Disposition": f'attachment; filename="{img["wp_name"]}"', "Content-Type": "image/png"},
        data=data, timeout=60)

    if r.status_code == 201:
        media = r.json()
        url = media['source_url']
        uploaded_urls[img['wp_name']] = url
        print(f"OK -> {url}")
        s.post(f"{BASE}/wp-json/wp/v2/media/{media['id']}", json={"alt_text": img["alt"], "caption": img["caption"]})
    else:
        print(f"FAILED ({r.status_code}): {r.text[:200]}")


def img(wp_name):
    return uploaded_urls.get(wp_name, f"{BASE}/wp-content/uploads/2026/03/{wp_name}")


# ============================================================
# STEP 2: Build page content
# ============================================================

print("\n=== Building page content ===\n")

page_content = '''<!-- wp:html -->
<style>
:root {{
  --ps-primary: #001F3F;
  --ps-accent: #2B6CB0;
  --ps-text: #1F2937;
  --ps-text-muted: #6B7280;
  --ps-card-bg: #f8fafc;
  --ps-border: #e5e7eb;
  --ps-success: #059669;
}}
.cas-step {{
  background: var(--ps-card-bg);
  border: 1px solid var(--ps-border);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}}
.cas-step h3 {{
  color: var(--ps-primary);
  margin: 0 0 12px 0;
  font-size: 1.2rem;
}}
.cas-step img {{
  width: 100%;
  border-radius: 8px;
  box-shadow: 0 3px 12px rgba(0,0,0,0.12);
  margin: 12px 0;
}}
.cas-step .caption {{
  color: var(--ps-text-muted);
  font-size: 0.85rem;
  font-style: italic;
  text-align: center;
  margin: 4px 0 12px;
}}
.cas-step p {{
  color: var(--ps-text);
  line-height: 1.6;
  margin: 8px 0;
}}
.cas-flow {{
  background: linear-gradient(135deg, #001F3F 0%, #0a3d6b 100%);
  border-radius: 12px;
  padding: 32px;
  margin: 32px 0;
  color: #fff;
}}
.cas-flow h3 {{
  color: #fff;
  margin: 0 0 16px;
  font-size: 1.3rem;
}}
.cas-flow-step {{
  background: rgba(255,255,255,0.1);
  border-radius: 8px;
  padding: 14px 18px;
  margin-bottom: 8px;
  font-size: 0.95rem;
  line-height: 1.5;
}}
.cas-flow-arrow {{
  text-align: center;
  font-size: 1.4rem;
  color: rgba(255,255,255,0.5);
  margin: 4px 0;
}}
.cas-mapping {{
  background: #f0f4f8;
  border-left: 4px solid var(--ps-accent);
  border-radius: 0 12px 12px 0;
  padding: 20px 24px;
  margin: 16px 0;
}}
.cas-mapping h4 {{
  color: var(--ps-primary);
  margin: 0 0 8px;
}}
.cas-mapping code {{
  background: #e2e8f0;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.85rem;
}}
.cas-table {{
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  font-size: 0.9rem;
}}
.cas-table th {{
  background: var(--ps-primary);
  color: #fff;
  padding: 10px 14px;
  text-align: left;
  font-weight: 600;
}}
.cas-table td {{
  padding: 8px 14px;
  border-bottom: 1px solid var(--ps-border);
  color: var(--ps-text);
}}
.cas-table tr:nth-child(even) {{
  background: #f8fafc;
}}
.cas-badge {{
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}}
.cas-badge-green {{ background: #d1fae5; color: #065f46; }}
.cas-badge-blue {{ background: #dbeafe; color: #1e40af; }}
.cas-badge-amber {{ background: #fef3c7; color: #92400e; }}
</style>
<!-- /wp:html -->

<!-- wp:html -->
<h2 style="text-align:center;padding:10px 0;margin:0;color:var(--ps-primary);font-size:2rem;font-weight:700;">Cross-Application Sync</h2>
<p style="text-align:center;color:var(--ps-accent);font-size:1.2rem;margin:0 0 8px;font-weight:500;">Dolibarr to Odoo Customer Sync via Dynamic Orchestration</p>
<p style="text-align:center;color:var(--ps-text-muted);font-size:0.9rem;margin:0 0 30px;">Demonstrated March 22, 2026 using PolySniffer, Mapping Engine, and RabbitMQ</p>

<div style="max-width:860px;margin:0 auto;padding:0 20px;">

<p style="color:var(--ps-text);font-size:1.05rem;line-height:1.8;margin-bottom:32px;">
This page documents a live demonstration of PolySaaS cross-application sync: creating a new customer in <strong>Dolibarr ERP</strong> and automatically synchronizing it to <strong>Odoo CRM</strong> as a contact/partner. The process uses <a href="{home}/polysniffer/" style="color:var(--ps-accent);">PolySniffer</a> for traffic capture, the <strong>Mapping Engine</strong> for field transformation, <strong>RabbitMQ</strong> as the message broker, and <a href="{home}/dynamic-orchestration/" style="color:var(--ps-accent);">Dynamic Orchestration</a> to wire it all together with zero code changes.
</p>

<div class="cas-flow">
<h3>End-to-End Data Flow</h3>
<div class="cas-flow-step"><strong>1.</strong> User creates customer in Dolibarr via Passthrough Proxy</div>
<div class="cas-flow-arrow">&#8595;</div>
<div class="cas-flow-step"><strong>2.</strong> Instruction A matches <code style="color:#93c5fd;">POST /societe/card.php</code></div>
<div class="cas-flow-arrow">&#8595;</div>
<div class="cas-flow-step"><strong>3.</strong> Mapping Engine extracts &amp; normalizes 21 fields from the POST body</div>
<div class="cas-flow-arrow">&#8595;</div>
<div class="cas-flow-step"><strong>4.</strong> Normalized event published to RabbitMQ (<code style="color:#93c5fd;">polysaas.crossapp.customer.created</code>)</div>
<div class="cas-flow-arrow">&#8595;</div>
<div class="cas-flow-step"><strong>5.</strong> MQ Monitor picks up message, triggers Instruction B</div>
<div class="cas-flow-arrow">&#8595;</div>
<div class="cas-flow-step"><strong>6.</strong> Mapping Engine transforms normalized data to 14 Odoo partner fields</div>
<div class="cas-flow-arrow">&#8595;</div>
<div class="cas-flow-step"><strong>7.</strong> Odoo XML-RPC: <code style="color:#93c5fd;">res.partner.create()</code> &mdash; customer appears in Odoo Contacts</div>
</div>

<h2 style="color:var(--ps-primary);font-size:1.5rem;margin:40px 0 20px;">Step-by-Step: Sniffing Dolibarr</h2>

<div class="cas-step">
<h3>Step 1 &mdash; Launch PolySniffer for Dolibarr</h3>
<p>In the Django admin, each PassThrough endpoint has a <strong>PolySniffer Analysis</strong> button. Click it on the Dolibarr ERP row to start the traffic capture proxy.</p>
<img src="{img_admin}" alt="PassThrough endpoint admin with PolySniffer Analysis button for Dolibarr">
<div class="caption">PassThrough endpoint list &mdash; Dolibarr ERP at localhost:8889 with PolySniffer Analysis</div>
</div>

<div class="cas-step">
<h3>Step 2 &mdash; PolySniffer Captures All Traffic</h3>
<p>The PolySniffer dashboard shows every HTTP request in real time. As we navigate Dolibarr, every GET and POST is captured with full headers, cookies, and body content.</p>
<img src="{img_sniffer}" alt="PolySniffer live capture dashboard with Dolibarr traffic entries">
<div class="caption">80+ requests captured during the Dolibarr session &mdash; login, navigation, CSS, JS, and the critical form POST</div>
</div>

<div class="cas-step">
<h3>Step 3 &mdash; Login to Dolibarr Through the Proxy</h3>
<p>Dolibarr 19.0.2 loads through the PolySniffer proxy. The login request is captured, giving us the CSRF token pattern and authentication flow.</p>
<img src="{img_login}" alt="Dolibarr 19.0.2 login screen">
<div class="caption">Dolibarr 19.0.2 login &mdash; admin credentials, all traffic passively captured</div>
</div>

<div class="cas-step">
<h3>Step 4 &mdash; Navigate to Third-parties</h3>
<p>After login, the Dolibarr dashboard shows the full menu: Home, Members, Third-parties, Products, Projects, Commerce, Billing, and more. We navigate to <strong>Third-parties</strong>.</p>
<img src="{img_setup}" alt="Dolibarr admin with Third-parties menu highlighted">
<div class="caption">Dolibarr navigation bar &mdash; Third-parties module selected</div>
</div>

<div class="cas-step">
<h3>Step 5 &mdash; Select New Customer</h3>
<p>The Third-parties sidebar shows the entity list. Statistics: 0 Prospects, 0 Customers, 0 Vendors. We click <strong>New Customer</strong> to begin.</p>
<img src="{img_thirdparties}" alt="Third-parties sidebar with New Customer highlighted">
<div class="caption">Zero existing records &mdash; this will be the first customer synced to Odoo</div>
</div>

<div class="cas-step">
<h3>Step 6 &mdash; Fill the New Third Party Form</h3>
<p>The form captures comprehensive customer data. We fill in the fields that will be extracted by the Mapping Engine:</p>
<img src="{img_form}" alt="Dolibarr New Third Party form filled with Mike Oliver data">
<div class="caption">Core fields: name, alias, prospect/customer classification, address, zip, city, phone</div>
<table class="cas-table">
<tr><th>Form Field</th><th>Value Entered</th><th>Normalized To</th></tr>
<tr><td>Third-party name</td><td>Mike Oliver</td><td><code>name</code></td></tr>
<tr><td>Alias</td><td>Mike Oliver</td><td><code>name_alias</code></td></tr>
<tr><td>Prospect / Customer</td><td>Prospect / Customer</td><td><code>is_customer = 1</code></td></tr>
<tr><td>Address</td><td>102 Woodlily Pl.</td><td><code>street</code></td></tr>
<tr><td>Zip Code</td><td>77382</td><td><code>zip</code></td></tr>
<tr><td>City</td><td>Spring</td><td><code>city</code></td></tr>
<tr><td>Phone</td><td>2818535769</td><td><code>phone</code></td></tr>
<tr><td>Email</td><td>mikeoliveraz@gmail.com</td><td><code>email</code></td></tr>
<tr><td>Third-party type</td><td>Workforce</td><td><code>typent_id</code></td></tr>
</table>
</div>

<div class="cas-step">
<h3>Step 7 &mdash; Submit: Create Third Party</h3>
<p>The bottom of the form shows Professional IDs, Sales tax (checked), Third-party type, and the sales representative assignment. Click <strong>CREATE THIRD PARTY</strong>.</p>
<img src="{img_submit}" alt="Create Third Party button at bottom of Dolibarr form">
<div class="caption">This POST triggers the entire cross-app sync chain</div>
<p>When submitted, PolySniffer captures the full POST body with all 43 form fields, including the hidden CSRF token, action type, and all visible form values.</p>
</div>

<div class="cas-step">
<h3>Step 8 &mdash; Customer Created in Dolibarr</h3>
<p>Dolibarr confirms the record with auto-generated Customer Code <strong>CU2603-00001</strong>. All entered data is displayed on the card view.</p>
<img src="{img_result}" alt="Mike Oliver customer card in Dolibarr showing all synced fields">
<div class="caption">Mike Oliver &mdash; Customer Code CU2603-00001, Type: Workforce, Prospect + Customer</div>
</div>

<h2 style="color:var(--ps-primary);font-size:1.5rem;margin:40px 0 20px;">Result: Customer in Odoo</h2>

<div class="cas-step">
<h3>Step 9 &mdash; Mike Oliver Appears in Odoo Contacts</h3>
<p>The sync chain completes: Dolibarr &rarr; Mapping Engine &rarr; RabbitMQ &rarr; Mapping Engine &rarr; Odoo XML-RPC. The customer record now appears in <strong>Odoo Contacts</strong>.</p>
<img src="{img_odoo_grid}" alt="Odoo Contacts grid view showing Mike Oliver synced from Dolibarr">
<div class="caption">Odoo Contacts grid &mdash; Mike Oliver (red arrow) appears alongside existing demo data, synced from Dolibarr</div>
</div>

<div class="cas-step">
<h3>Step 10 &mdash; Full Record Detail in Odoo</h3>
<p>Opening the contact record confirms every field was correctly mapped from the Dolibarr form through both Mapping Engine transformations:</p>
<img src="{img_odoo_detail}" alt="Odoo Contact detail page for Mike Oliver showing all synced fields">
<div class="caption">All fields intact: name, address (102 Woodlily Pl., Spring, 77382), phone, mobile, email</div>
<table class="cas-table">
<tr><th>Dolibarr Field</th><th>Normalized</th><th>Odoo Field</th><th>Value</th></tr>
<tr><td>name</td><td>name</td><td>name</td><td>Mike Oliver</td></tr>
<tr><td>address</td><td>street</td><td>street</td><td>102 Woodlily Pl.</td></tr>
<tr><td>zipcode</td><td>zip</td><td>zip</td><td>77382</td></tr>
<tr><td>town</td><td>city</td><td>city</td><td>Spring</td></tr>
<tr><td>phone</td><td>phone</td><td>phone</td><td>2818535769</td></tr>
<tr><td>fax</td><td>fax</td><td>mobile</td><td>2818535769</td></tr>
<tr><td>email</td><td>email</td><td>email</td><td>mikeoliveraz@gmail.com</td></tr>
<tr><td>customer_code</td><td>customer_code</td><td>ref</td><td>CU2603-00001</td></tr>
</table>
<p style="margin-top:12px;"><span class="cas-badge cas-badge-green">Sync Complete</span> &mdash; Zero code changes. Entirely driven by database-configured Mappings and Instructions.</p>
</div>

<h2 style="color:var(--ps-primary);font-size:1.5rem;margin:40px 0 20px;">Instructions: The Routing Rules</h2>

<div class="cas-step">
<h3>Instructions in the Tenant Admin</h3>
<p>Instructions are the routing rules that connect incoming requests to atomic services. In the <strong>Oliver Enterprises</strong> tenant, two new Instructions were created for the cross-app sync flow:</p>
<img src="{img_instr_list}" alt="Django admin Instructions list in olient tenant">
<div class="caption">Three Instructions in the olient tenant &mdash; the two new entries route Dolibarr POST and MQ messages to their respective services</div>
<table class="cas-table">
<tr><th>Request Path</th><th>Method</th><th>Service</th><th>Purpose</th></tr>
<tr><td><code>/societe/card.php</code></td><td>POST</td><td>EndpointDataExtractor</td><td>Captures Dolibarr form POST, extracts &amp; publishes to RabbitMQ</td></tr>
<tr><td><code>/mq/polysaas.crossapp.customer.created</code></td><td>POST</td><td>OdooCustomerSync</td><td>Picks up MQ message, maps to Odoo partner, syncs via XML-RPC</td></tr>
</table>
</div>

<div class="cas-step">
<h3>Instruction Detail: Dolibarr POST Capture</h3>
<p>Each Instruction defines a <strong>requestpath</strong> (substring match), <strong>method</strong>, <strong>direction</strong>, and an <strong>eventKey</strong> for tracking. The <strong>Instruction Mappings</strong> tab links it to one or more Mapping records that define the field extraction logic.</p>
<img src="{img_instr_detail}" alt="Instruction detail for Dolibarr POST capture">
<div class="caption">Instruction detail: requestpath <code>/societe/card.php</code>, eventKey <code>dolibarr.customer.created</code>, method POST, direction REQUEST</div>
<p>When any POST request passes through the proxy and its URL contains <code>/societe/card.php</code>, this Instruction fires the <strong>EndpointDataExtractor</strong>, which uses the attached Mapping to extract and normalize the form fields.</p>
</div>

<!-- MAPPING ENGINE SECTION -->
<h2 style="color:var(--ps-primary);font-size:1.5rem;margin:40px 0 20px;">The Mapping Engine</h2>

<p style="color:var(--ps-text);line-height:1.7;">The Mapping Engine is database-driven &mdash; no code changes needed to add new integrations. Each mapping defines how to transform fields using an <strong>expression syntax</strong> with pipe operators:</p>

<div class="cas-mapping">
<h4>Mapping 1: Dolibarr POST &rarr; Normalized Event</h4>
<p>Direction: <span class="cas-badge cas-badge-blue">SOURCE &rarr; NORMALIZED</span></p>
<p>Extracts Dolibarr form fields and normalizes them into a cross-application customer event:</p>
<table class="cas-table">
<tr><th>Normalized Field</th><th>Expression</th><th>Result</th></tr>
<tr><td><code>name</code></td><td><code>request.POST.name|strip</code></td><td>Mike Oliver</td></tr>
<tr><td><code>email</code></td><td><code>request.POST.email|strip|lower|email</code></td><td>mikeoliveraz@gmail.com</td></tr>
<tr><td><code>phone</code></td><td><code>request.POST.phone|strip|default:None</code></td><td>2818535769</td></tr>
<tr><td><code>street</code></td><td><code>request.POST.address|strip</code></td><td>102 Woodlily Pl.</td></tr>
<tr><td><code>zip</code></td><td><code>request.POST.zipcode|strip</code></td><td>77382</td></tr>
<tr><td><code>city</code></td><td><code>request.POST.town|strip</code></td><td>Spring</td></tr>
<tr><td><code>is_customer</code></td><td><code>request.POST.client|int:1:0</code></td><td>1</td></tr>
<tr><td><code>customer_code</code></td><td><code>request.POST.customer_code|strip</code></td><td>CU2603-00001</td></tr>
</table>
</div>

<div class="cas-mapping">
<h4>Mapping 2: Normalized &rarr; Odoo res.partner</h4>
<p>Direction: <span class="cas-badge cas-badge-green">NORMALIZED &rarr; TARGET</span></p>
<p>Transforms the normalized event into Odoo-specific partner fields for XML-RPC sync:</p>
<table class="cas-table">
<tr><th>Odoo Field</th><th>Expression</th><th>Result</th></tr>
<tr><td><code>name</code></td><td><code>payload.name</code></td><td>Mike Oliver</td></tr>
<tr><td><code>email</code></td><td><code>payload.email</code></td><td>mikeoliveraz@gmail.com</td></tr>
<tr><td><code>customer_rank</code></td><td><code>payload.is_customer|int:1:0</code></td><td>1</td></tr>
<tr><td><code>ref</code></td><td><code>payload.customer_code|default:None</code></td><td>CU2603-00001</td></tr>
<tr><td><code>is_company</code></td><td><code>'True'|bool</code></td><td>True</td></tr>
<tr><td><code>street</code></td><td><code>payload.street</code></td><td>102 Woodlily Pl.</td></tr>
<tr><td><code>city</code></td><td><code>payload.city</code></td><td>Spring</td></tr>
</table>
</div>

<p style="color:var(--ps-text);line-height:1.7;">Pipe operators include: <code>|strip</code>, <code>|lower</code>, <code>|upper</code>, <code>|email</code> (validate), <code>|int:1:0</code> (conditional cast), <code>|default:value</code>, <code>|truncate:120</code>, <code>|prefix:DOL-</code>, <code>|bool</code>, <code>|if:path</code>, and <code>|coalesce:fallback.path</code>. All configurable from the admin &mdash; no deployment needed.</p>

<h2 style="color:var(--ps-primary);font-size:1.5rem;margin:40px 0 20px;">Technology Stack</h2>

<table class="cas-table">
<tr><th>Component</th><th>Role</th><th>Status</th></tr>
<tr><td><strong>PolySniffer</strong></td><td>Passive traffic capture to discover form fields and POST paths</td><td><span class="cas-badge cas-badge-green">Active</span></td></tr>
<tr><td><strong>Mapping Engine</strong></td><td>Database-driven field extraction and transformation with pipe expressions</td><td><span class="cas-badge cas-badge-green">Active</span></td></tr>
<tr><td><strong>RabbitMQ</strong></td><td>Message broker between source extraction and target sync services</td><td><span class="cas-badge cas-badge-green">Active</span></td></tr>
<tr><td><strong>Atomic Services</strong></td><td>EndpointDataExtractor + OdooCustomerSync</td><td><span class="cas-badge cas-badge-green">Active</span></td></tr>
<tr><td><strong>Instructions</strong></td><td>Path-based routing: <code>/societe/card.php</code> and <code>/mq/...</code></td><td><span class="cas-badge cas-badge-green">Active</span></td></tr>
<tr><td><strong>Passthrough Proxy</strong></td><td>Transparent proxy for accessing Dolibarr through PolySaaS</td><td><span class="cas-badge cas-badge-amber">Handler Pending</span></td></tr>
<tr><td><strong>Odoo XML-RPC</strong></td><td>Creates/updates res.partner records in Odoo CRM</td><td><span class="cas-badge cas-badge-green">Active</span></td></tr>
</table>

<div style="text-align:center;padding:40px 0 20px;">
<p style="color:var(--ps-text);font-size:1.1rem;margin-bottom:20px;">Cross-application sync is just one example of what Dynamic Orchestration enables.</p>
<a href="{home}/dynamic-orchestration/" style="display:inline-block;background:var(--ps-accent);color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:1rem;margin:0 8px;">Dynamic Orchestration</a>
<a href="{home}/polysniffer/" style="display:inline-block;background:var(--ps-primary);color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:1rem;margin:0 8px;">PolySniffer</a>
<a href="{home}/schedule-demo/" style="display:inline-block;background:var(--ps-success);color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:1rem;margin:0 8px;">Schedule a Demo</a>
</div>

</div>
<!-- /wp:html -->'''.format(
    home=BASE,
    img_sniffer=img("crossapp-polysniffer-dolibarr-capture.png"),
    img_admin=img("crossapp-passthrough-endpoints-admin.png"),
    img_login=img("crossapp-dolibarr-login.png"),
    img_setup=img("crossapp-dolibarr-setup-thirdparties.png"),
    img_thirdparties=img("crossapp-dolibarr-thirdparties-menu.png"),
    img_form=img("crossapp-dolibarr-new-thirdparty-form.png"),
    img_submit=img("crossapp-dolibarr-create-thirdparty-submit.png"),
    img_result=img("crossapp-dolibarr-customer-created.png"),
    img_odoo_grid=img("crossapp-odoo-contacts-grid-mike-oliver.png"),
    img_odoo_detail=img("crossapp-odoo-contact-mike-oliver-detail.png"),
    img_instr_list=img("crossapp-instruction-list-olient.png"),
    img_instr_detail=img("crossapp-instruction-detail-dolibarr.png"),
)


# ============================================================
# STEP 3: Create or update the page on polysaas.online
# ============================================================

print("=== Creating/updating page on polysaas.online ===\n")

SLUG = "cross-app-sync"
SYNC_PAGE_URL = BASE + "/cross-app-sync/"

r = s.get(BASE + "/wp-json/wp/v2/pages", params={
    "slug": SLUG, "context": "edit", "_fields": "id,slug,title,status",
    "status": "publish,draft,private,pending,trash"
})
existing = r.json()

if existing:
    pid = existing[0]['id']
    print(f"Page exists (id={pid}), updating...")
    r2 = s.post(BASE + f"/wp-json/wp/v2/pages/{pid}", json={
        "content": page_content, "title": "Cross-Application Sync", "status": "publish"})
else:
    print("Creating new page...")
    r2 = s.post(BASE + "/wp-json/wp/v2/pages", json={
        "slug": SLUG, "content": page_content, "title": "Cross-Application Sync", "status": "publish", "template": ""})

if r2.status_code in (200, 201):
    result = r2.json()
    print(f"  OK: id={result['id']}, slug={result['slug']}")
    print(f"  URL: {result.get('link', 'N/A')}")
else:
    print(f"  FAILED: {r2.status_code} {r2.text[:300]}")


# ============================================================
# STEP 4: Update Dynamic Orchestration page to link here
# ============================================================

print("\n=== Updating Dynamic Orchestration page ===\n")

r = s.get(BASE + "/wp-json/wp/v2/pages", params={
    "slug": "dynamic-orchestration", "context": "edit", "_fields": "id,slug,content"})
dyn_pages = r.json()

if dyn_pages:
    dp = dyn_pages[0]
    content = dp['content']['raw']
    link_html = (
        '\n<!-- wp:html -->\n'
        '<div style="background:linear-gradient(135deg,#f0f4f8,#e8edf2);border:2px solid var(--ps-accent,#2B6CB0);border-radius:12px;padding:24px;margin:24px auto;max-width:800px;text-align:center;">\n'
        '<h3 style="color:var(--ps-primary,#001F3F);margin:0 0 8px;">See It In Action</h3>\n'
        '<p style="color:var(--ps-text,#1F2937);margin:0 0 16px;line-height:1.6;">Watch Dynamic Orchestration sync a new Dolibarr customer to Odoo CRM in real time &mdash; using PolySniffer, the Mapping Engine, and RabbitMQ.</p>\n'
        '<a href="' + SYNC_PAGE_URL + '" style="display:inline-block;background:var(--ps-accent,#2B6CB0);color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;">Cross-Application Sync Demo &rarr;</a>\n'
        '</div>\n'
        '<!-- /wp:html -->\n'
    )
    if 'cross-app-sync' not in content:
        cta_idx = content.find('Sign Up for a Demo')
        if cta_idx > 0:
            block_start = content.rfind('<!-- wp:html -->', 0, cta_idx)
            insert_at = block_start if block_start > 0 else cta_idx
            new_content = content[:insert_at] + link_html + content[insert_at:]
        else:
            new_content = content + link_html
        r2 = s.post(BASE + f"/wp-json/wp/v2/pages/{dp['id']}", json={"content": new_content})
        print(f"  {'OK' if r2.status_code == 200 else 'FAILED'}: Added link to Dynamic Orchestration page")
    else:
        print("  Link already present, skipping")
else:
    print("  Dynamic Orchestration page not found")


# ============================================================
# STEP 5: Update PolySniffer page to link here
# ============================================================

print("\n=== Updating PolySniffer page ===\n")

r = s.get(BASE + "/wp-json/wp/v2/pages", params={
    "slug": "polysniffer", "context": "edit", "_fields": "id,slug,content"})
sniffer_pages = r.json()

if sniffer_pages:
    sp = sniffer_pages[0]
    content = sp['content']['raw']
    link_html = (
        '\n<!-- wp:html -->\n'
        '<div style="background:linear-gradient(135deg,#f0f4f8,#e8edf2);border:2px solid var(--ps-accent,#2B6CB0);border-radius:12px;padding:24px;margin:24px auto;max-width:800px;text-align:center;">\n'
        '<h3 style="color:var(--ps-primary,#001F3F);margin:0 0 8px;">PolySniffer in Action</h3>\n'
        '<p style="color:var(--ps-text,#1F2937);margin:0 0 16px;line-height:1.6;">See how PolySniffer captured Dolibarr&rsquo;s new customer form POST and enabled automatic sync to Odoo CRM &mdash; all through Dynamic Orchestration.</p>\n'
        '<a href="' + SYNC_PAGE_URL + '" style="display:inline-block;background:var(--ps-accent,#2B6CB0);color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;">Cross-Application Sync Demo &rarr;</a>\n'
        '</div>\n'
        '<!-- /wp:html -->\n'
    )
    if 'cross-app-sync' not in content:
        cta_idx = content.find('Sign Up for a Demo')
        if cta_idx > 0:
            block_start = content.rfind('<!-- wp:html -->', 0, cta_idx)
            insert_at = block_start if block_start > 0 else cta_idx
            new_content = content[:insert_at] + link_html + content[insert_at:]
        else:
            new_content = content + link_html
        r2 = s.post(BASE + f"/wp-json/wp/v2/pages/{sp['id']}", json={"content": new_content})
        print(f"  {'OK' if r2.status_code == 200 else 'FAILED'}: Added link to PolySniffer page")
    else:
        print("  Link already present, skipping")
else:
    print("  PolySniffer page not found")

print(f"\n=== Done ===")
print(f"Cross-App Sync page: {SYNC_PAGE_URL}")
