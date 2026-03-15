"""
Step 1: Download meaningful images from polysaas.online
Step 2: Upload to Azure WordPress media library
Step 3: Inject into appropriate detail pages
"""
import requests, re, sys, os, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
PROD = "https://polysaas.online"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Images to migrate: (prod_url, filename, target_page_slug, description)
IMAGES = [
    # Application pages
    (f"{PROD}/wp-content/uploads/2026/02/odoo-apps-1024x682.png",
     "odoo-apps.png", "odoo", "Odoo application suite grid"),
    (f"{PROD}/wp-content/uploads/2026/02/nextCloudDashboard3.png",
     "nextcloud-dashboard.png", "nextcloud", "Nextcloud dashboard interface"),
    (f"{PROD}/wp-content/uploads/2026/02/folibarr-dashboard-1024x576.png",
     "dolibarr-dashboard.png", "dolibarr-3", "Dolibarr ERP dashboard"),
    (f"{PROD}/wp-content/uploads/2025/12/Falcon-on-GCP.png",
     "polysysmon-falcon-gcp.png", "polysysmon", "PolySysMon Falcon on GCP architecture"),
    (f"{PROD}/wp-content/uploads/2025/12/Network-Diagram-Rinith10-780552-1.png",
     "polysysmon-network-diagram.png", "polysysmon", "Network monitoring diagram"),
    (f"{PROD}/wp-content/uploads/2026/01/PlySysMon-1024x463.jpg",
     "polysysmon-dashboard.jpg", "polysysmon", "PolySysMon monitoring dashboard"),
    # Feature pages
    (f"{PROD}/wp-content/uploads/2026/02/PolySaaS-GCP.drawio-1-1024x698.png",
     "polysaas-gcp-architecture.png", "architecture", "PolySaaS GCP architecture diagram"),
    (f"{PROD}/wp-content/uploads/2026/02/Fynami-Orchestrtion-Simple-Sequence.drawio.png",
     "dynamic-orchestration-sequence.png", "architecture", "Dynamic orchestration sequence diagram"),
    (f"{PROD}/wp-content/uploads/2026/02/why-It-Matters-1024x787.png",
     "why-it-matters-diagram.png", "architecture", "Why it matters diagram"),
    (f"{PROD}/wp-content/uploads/2026/02/Event-Driven-Architecture.jpeg",
     "event-driven-architecture.jpg", "dynamic-orchestration", "Event-driven architecture diagram"),
    (f"{PROD}/wp-content/uploads/2026/02/Mike_Oliver_minimalist_Customer_signs_up_in_HubSpot__PolySaaS_af61130d-c19d-47d1-81a0-4660421d53ed_3.png",
     "dynamic-orchestration-hubspot-flow.png", "dynamic-orchestration", "Customer signup orchestration flow"),
    (f"{PROD}/wp-content/uploads/2026/01/A-service-network-involving-various-cloud-computing-services_Q320.jpg",
     "atomic-services-cloud-network.jpg", "atomic-services", "Cloud computing services network"),
    (f"{PROD}/wp-content/uploads/2026/02/bundled-Applications-1.png",
     "bundled-applications-overview.png", "bundled-applications", "Bundled applications overview diagram"),
]

# Download and upload
uploaded = {}  # filename -> azure_url
os.makedirs("d:/PolySaaS/temp_imgs", exist_ok=True)

for prod_url, filename, target, desc in IMAGES:
    print(f"\n--- {filename} ---")
    
    # Download from prod
    try:
        r = requests.get(prod_url, timeout=30)
        if r.status_code != 200:
            print(f"  Download FAILED: {r.status_code}")
            continue
        
        local_path = f"d:/PolySaaS/temp_imgs/{filename}"
        with open(local_path, 'wb') as f:
            f.write(r.content)
        print(f"  Downloaded: {len(r.content)} bytes")
        
        # Detect content type
        ct = r.headers.get('Content-Type', 'image/png')
        if 'jpeg' in ct or 'jpg' in ct or filename.endswith('.jpg'):
            ct = 'image/jpeg'
        else:
            ct = 'image/png'
        
        # Upload to Azure
        with open(local_path, 'rb') as f:
            data = f.read()
        
        r2 = s.post(f"{AZURE}/wp-json/wp/v2/media",
            headers={"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": ct},
            data=data)
        
        if r2.status_code == 201:
            azure_url = r2.json()['source_url']
            azure_id = r2.json()['id']
            uploaded[filename] = azure_url
            print(f"  Uploaded: id={azure_id} -> {azure_url}")
        else:
            print(f"  Upload FAILED: {r2.status_code} - {r2.text[:200]}")
    
    except Exception as e:
        print(f"  ERROR: {e}")

print(f"\n{'='*60}")
print(f"Successfully uploaded: {len(uploaded)} / {len(IMAGES)}")
for fn, url in uploaded.items():
    print(f"  {fn}: {url}")

# Save mapping for next step
import json
with open("d:/PolySaaS/uploaded_images.json", "w") as f:
    json.dump(uploaded, f, indent=2)
print(f"\nMapping saved to uploaded_images.json")
