"""
Upload Instruction screenshots to WordPress and add them to the Cross-App Sync page.
"""
import requests, sys, os, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

ASSETS = r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets"

IMAGES = [
    {
        "src": os.path.join(ASSETS, "c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_image-5f6b435e-389d-4dd5-8645-06f5ebd5a779.png"),
        "wp_name": "crossapp-instruction-list-olient.png",
        "alt": "Django admin Instructions list in olient tenant showing cross-app sync entries",
        "caption": "Instructions list in Oliver Enterprises tenant: Dolibarr POST capture and MQ-to-Odoo sync",
    },
    {
        "src": os.path.join(ASSETS, "c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_image-4433a229-7f52-4de7-bef8-d409f2adfee1.png"),
        "wp_name": "crossapp-instruction-detail-dolibarr.png",
        "alt": "Django admin Instruction detail for Dolibarr POST capture showing requestpath and eventKey",
        "caption": "Instruction detail: /societe/card.php POST with eventKey dolibarr.customer.created",
    },
]

uploaded_urls = {}
print("=== Uploading Instruction screenshots ===\n")

for img in IMAGES:
    if not os.path.exists(img["src"]):
        print(f"  SKIP: {img['wp_name']} - source not found")
        continue

    with open(img["src"], "rb") as f:
        data = f.read()

    print(f"  Uploading {img['wp_name']} ({len(data)//1024}KB)...", end=" ")

    r = s.post(
        f"{AZURE}/wp-json/wp/v2/media",
        headers={
            "Content-Disposition": f'attachment; filename="{img["wp_name"]}"',
            "Content-Type": "image/png",
        },
        data=data
    )

    if r.status_code == 201:
        media = r.json()
        url = media['source_url']
        uploaded_urls[img['wp_name']] = url
        print(f"OK -> {url}")
        s.post(f"{AZURE}/wp-json/wp/v2/media/{media['id']}", json={
            "alt_text": img["alt"],
            "caption": img["caption"],
        })
    else:
        print(f"FAILED ({r.status_code}): {r.text[:200]}")


def img_url(wp_name):
    return uploaded_urls.get(wp_name, f"{AZURE}/wp-content/uploads/2026/03/{wp_name}")


# === Fetch current page content ===
print("\n=== Updating Cross-App Sync page ===\n")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "cross-app-sync", "context": "edit", "_fields": "id,slug,content"
})
pages = r.json()
if not pages:
    print("ERROR: Cross-App Sync page not found!")
    sys.exit(1)

page = pages[0]
content = page['content']['raw']
pid = page['id']
print(f"Page found: id={pid}")

# === Build new section HTML ===
instr_section = (
    '<h2 style="color:var(--ps-primary);font-size:1.5rem;margin:40px 0 20px;">Instructions: The Routing Rules</h2>\n'
    '\n'
    '<div class="cas-step">\n'
    '<h3>Instructions in the Tenant Admin</h3>\n'
    '<p>Instructions are the routing rules that connect incoming requests to atomic services. '
    'In the <strong>Oliver Enterprises</strong> tenant, two new Instructions were created for the cross-app sync flow:</p>\n'
    '<img src="' + img_url("crossapp-instruction-list-olient.png") + '" alt="Django admin Instructions list in olient tenant">\n'
    '<div class="caption">Three Instructions in the olient tenant &mdash; the two new entries route Dolibarr POST and MQ messages to their respective services</div>\n'
    '\n'
    '<table class="cas-table">\n'
    '<tr><th>Request Path</th><th>Method</th><th>Service</th><th>Purpose</th></tr>\n'
    '<tr><td><code>/societe/card.php</code></td><td>POST</td><td>EndpointDataExtractor</td><td>Captures Dolibarr form POST, extracts &amp; publishes to RabbitMQ</td></tr>\n'
    '<tr><td><code>/mq/polysaas.crossapp.customer.created</code></td><td>POST</td><td>OdooCustomerSync</td><td>Picks up MQ message, maps to Odoo partner, syncs via XML-RPC</td></tr>\n'
    '</table>\n'
    '</div>\n'
    '\n'
    '<div class="cas-step">\n'
    '<h3>Instruction Detail: Dolibarr POST Capture</h3>\n'
    '<p>Each Instruction defines a <strong>requestpath</strong> (substring match), <strong>method</strong>, <strong>direction</strong>, and an <strong>eventKey</strong> for tracking. '
    'The <strong>Instruction Mappings</strong> tab links it to one or more Mapping records that define the field extraction logic.</p>\n'
    '<img src="' + img_url("crossapp-instruction-detail-dolibarr.png") + '" alt="Instruction detail for Dolibarr POST capture">\n'
    '<div class="caption">Instruction detail: requestpath <code>/societe/card.php</code>, eventKey <code>dolibarr.customer.created</code>, method POST, direction REQUEST</div>\n'
    '<p>When any POST request passes through the proxy and its URL contains <code>/societe/card.php</code>, this Instruction fires the <strong>EndpointDataExtractor</strong>, '
    'which uses the attached Mapping to extract and normalize the form fields.</p>\n'
    '</div>\n'
)

# Insert before "The Mapping Engine" section
marker = '<!-- MAPPING ENGINE SECTION -->'
if marker in content:
    insert_pos = content.index(marker)
    # Check if instruction section already exists
    if 'Instructions: The Routing Rules' not in content:
        new_content = content[:insert_pos] + instr_section + '\n' + content[insert_pos:]
        print("Inserting Instruction section before Mapping Engine section...")
    else:
        # Replace existing
        start = content.index('<h2 style="color:var(--ps-primary);font-size:1.5rem;margin:40px 0 20px;">Instructions: The Routing Rules')
        new_content = content[:start] + instr_section + '\n' + content[insert_pos:]
        print("Replacing existing Instruction section...")
else:
    print("WARNING: Mapping Engine marker not found, appending to end")
    new_content = content + '\n' + instr_section

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
if r2.status_code == 200:
    print(f"  OK: Page updated")
else:
    print(f"  FAILED: {r2.status_code} {r2.text[:300]}")

print(f"\nPage URL: {AZURE}/cross-app-sync/")
print("Done.")
