"""
Inject uploaded images into Azure detail pages.
Each image goes after the page subtitle/hero area, before Key Capabilities.
For pages with multiple images, they go in sequence.
"""
import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Image injection plan: page_slug -> [(url, alt, caption)]
AZ = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03"

INJECTIONS = {
    "odoo": [
        (f"{AZ}/odoo-apps.png", "Odoo Application Suite", "Odoo's comprehensive app ecosystem — ERP, CRM, accounting, inventory, and more"),
    ],
    "nextcloud": [
        (f"{AZ}/nextcloud-dashboard.png", "Nextcloud Dashboard", "Nextcloud Hub dashboard — files, calendar, contacts, and collaboration in one place"),
    ],
    "dolibarr-3": [
        (f"{AZ}/dolibarr-dashboard.png", "Dolibarr ERP Dashboard", "Dolibarr ERP dashboard — invoicing, inventory, and customer management"),
    ],
    "polysysmon": [
        (f"{AZ}/polysysmon-falcon-gcp.png", "PolySysMon on GCP", "PolySysMon agent architecture running on Google Cloud Platform"),
        (f"{AZ}/polysysmon-network-diagram.png", "Network Monitoring Diagram", "Network topology monitored by PolySysMon agents"),
        (f"{AZ}/polysysmon-dashboard.jpg", "PolySysMon Dashboard", "PolySysMon real-time monitoring dashboard"),
    ],
    "architecture": [
        (f"{AZ}/polysaas-gcp-architecture.png", "PolySaaS GCP Architecture", "PolySaaS cloud-native architecture on Google Cloud Platform"),
        (f"{AZ}/dynamic-orchestration-sequence.png", "Dynamic Orchestration Sequence", "Dynamic orchestration — simple sequence flow"),
        (f"{AZ}/why-it-matters-diagram.png", "Why It Matters", "Why dynamic orchestration matters for enterprise workflows"),
    ],
    "dynamic-orchestration": [
        (f"{AZ}/event-driven-architecture.jpg", "Event-Driven Architecture", "Event-driven architecture powering dynamic orchestration"),
        (f"{AZ}/dynamic-orchestration-hubspot-flow.png", "Customer Signup Flow", "Example: Customer signs up in HubSpot, PolySaaS orchestrates the workflow"),
    ],
    "atomic-services": [
        (f"{AZ}/atomic-services-cloud-network.jpg", "Cloud Services Network", "Interconnected cloud computing services via atomic service endpoints"),
    ],
    "bundled-applications": [
        (f"{AZ}/bundled-applications-overview.png", "Bundled Applications Overview", "All PolySaaS bundled applications at a glance"),
    ],
}

# Get all pages
pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
}).json()
page_map = {p['slug']: p for p in pages}

for slug, images in INJECTIONS.items():
    page = page_map.get(slug)
    if not page:
        print(f"  {slug}: PAGE NOT FOUND")
        continue
    
    raw = page['content']['raw']
    
    # Build the image block(s)
    img_html_parts = []
    for url, alt, caption in images:
        img_html_parts.append(f'''<div style="text-align:center;margin:20px auto;">
<img src="{url}" alt="{alt}" style="width:100%;max-width:800px;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="color:var(--ps-muted,#6B7280);font-size:0.85rem;margin-top:8px;font-style:italic;">{caption}</p>
</div>''')
    
    img_block = "\n".join(img_html_parts)
    
    # Find insertion point: after subtitle, before "Key Capabilities"
    # Strategy: find "Key Capabilities" heading and insert before it
    key_cap_idx = raw.find('Key Capabilities')
    if key_cap_idx < 0:
        key_cap_idx = raw.find('Key Features')
    
    if key_cap_idx > 0:
        # Find the start of the element containing "Key Capabilities"
        # Go back to find the <h2 or <div before it
        insert_before = raw.rfind('<h2', max(0, key_cap_idx - 100), key_cap_idx)
        if insert_before < 0:
            insert_before = raw.rfind('<div', max(0, key_cap_idx - 50), key_cap_idx)
        if insert_before < 0:
            insert_before = key_cap_idx
        
        new_raw = raw[:insert_before] + img_block + "\n" + raw[insert_before:]
    else:
        # No Key Capabilities - insert after subtitle/hero
        # Find end of first content heading (h2 subtitle)
        subtitle_end = raw.find('</p>', raw.find('font-weight:500')) 
        if subtitle_end > 0:
            insert_after = subtitle_end + 4
            new_raw = raw[:insert_after] + "\n" + img_block + "\n" + raw[insert_after:]
        else:
            # Fallback: insert after the page icon if present, or after toggle
            toggle_end = raw.rfind('<!-- /wp:html -->', 0, len(raw)//3)
            if toggle_end > 0:
                insert_after = toggle_end + len('<!-- /wp:html -->')
                new_raw = raw[:insert_after] + "\n<!-- wp:html -->\n" + img_block + "\n<!-- /wp:html -->\n" + raw[insert_after:]
            else:
                print(f"  {slug}: Could not find insertion point!")
                continue
    
    r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page['id']}", json={"content": new_raw})
    img_count = len(images)
    print(f"  {slug}: {r.status_code} ({img_count} image{'s' if img_count > 1 else ''})")

print("\nDone!")
