"""
Add two-column image section to Portal page:
- Left: Liferay portal dashboard
- Right: DOSE admin dashboard
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

LIFERAY_IMG = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/liferay-portal-dashboard.png"
DOSE_ADMIN_IMG = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2025/12/Welcome-to-the-D-O-S-E-Administration-D-O-S-E-Administration-12-13-2025_02_26_PM.png"
DOSE_SUBSCRIBE_IMG = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/02/Dose-Multi-Tenant-System-02-25-2026_12_18_PM-subcribe-full-page-scaled.png"

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "portal", "context": "edit", "_fields": "id,content"
}).json()
page = pages[0]
raw = page['content']['raw']

portal_block = f'''<div style="margin:24px auto;max-width:900px;">
<h2 style="text-align:center;color:var(--ps-primary,#001F3F);font-size:1.4rem;font-weight:600;margin-bottom:20px;">Portal Capabilities</h2>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;">

<div style="text-align:center;">
<h3 style="color:var(--ps-primary,#001F3F);font-size:1.1rem;font-weight:600;margin-bottom:12px;">Liferay Enterprise Portal</h3>
<img src="{LIFERAY_IMG}" alt="Liferay Portal Dashboard" style="width:100%;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="color:var(--ps-muted,#6B7280);font-size:0.82rem;margin-top:8px;font-style:italic;">Content delivery, widget management, and personalized user experiences</p>
</div>

<div style="text-align:center;">
<h3 style="color:var(--ps-primary,#001F3F);font-size:1.1rem;font-weight:600;margin-bottom:12px;">DOSE Admin Dashboard</h3>
<img src="{DOSE_ADMIN_IMG}" alt="DOSE Administration Dashboard" style="width:100%;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="color:var(--ps-muted,#6B7280);font-size:0.82rem;margin-top:8px;font-style:italic;">PolySaaS DOSE administration — tenant management, endpoints, and orchestration control</p>
</div>

</div>

<div style="text-align:center;margin-top:24px;">
<img src="{DOSE_SUBSCRIBE_IMG}" alt="DOSE Multi-Tenant Subscribe Page" style="width:100%;max-width:800px;border-radius:10px;box-shadow:0 3px 15px rgba(0,0,0,0.1);">
<p style="color:var(--ps-muted,#6B7280);font-size:0.82rem;margin-top:8px;font-style:italic;">DOSE multi-tenant subscription portal — self-service onboarding for new tenants</p>
</div>
</div>

<style>
@media (max-width:768px) {{
  div[style*="grid-template-columns:1fr 1fr"] {{ grid-template-columns: 1fr !important; }}
}}
</style>'''

key_cap_idx = raw.find('Key Capabilities')
if key_cap_idx > 0:
    insert_before = raw.rfind('<h2', max(0, key_cap_idx - 100), key_cap_idx)
    if insert_before < 0:
        insert_before = key_cap_idx
    new_raw = raw[:insert_before] + portal_block + "\n" + raw[insert_before:]
else:
    subtitle_end = raw.find('</p>', raw.find('font-weight:500'))
    if subtitle_end > 0:
        new_raw = raw[:subtitle_end+4] + "\n" + portal_block + "\n" + raw[subtitle_end+4:]
    else:
        print("Could not find insertion point")
        sys.exit(1)

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{page['id']}", json={"content": new_raw})
print(f"Update Portal page: {r2.status_code}")
if r2.status_code == 200:
    print("Portal page updated with two-column Liferay + DOSE layout")
