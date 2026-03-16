"""
Create and assign widgets to Kadence footer sidebar areas (footer1, footer2, footer3).
The Kadence footer builder has footer-widget1, footer-widget2, footer-widget3
assigned to the middle row columns. These correspond to sidebar areas
footer1, footer2, footer3.
"""
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Footer content split into 3 widgets

# Widget 1: CTA + Contact Info (for footer1/middle-left)
footer1_html = '''<div style="padding:20px 0;">
<h3 style="color:#5eead4;font-size:1.1rem;font-weight:600;margin-bottom:4px;text-align:center;">Stop Managing Tools. Start Orchestrating Them.</h3>
<p style="color:#94a3b8;text-align:center;font-size:0.9rem;margin-bottom:12px;">Join enterprises already running smarter with PolySaaS.</p>
<div style="text-align:center;margin-bottom:20px;">
<a href="/subscribe/" style="background:#2563eb;color:#fff;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:600;font-size:0.95rem;">Sign Up for a Demo</a>
</div>
<div style="display:flex;align-items:center;gap:14px;margin-bottom:12px;flex-wrap:wrap;justify-content:center;">
<img src="https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2025/03/logopolysaas_tr.png" alt="PolySaaS" style="width:70px;height:70px;border-radius:50%;background:#0a0a0a;padding:4px;">
<div style="color:#e5e7eb;font-style:italic;font-size:0.85rem;">5900 Balcones Drive Suite 100<br>Austin, TX 78731</div>
</div>
<p style="margin:4px 0;text-align:center;"><a href="mailto:michael.oliver@polysaas.online" style="color:#5eead4;text-decoration:none;font-size:0.85rem;">michael.oliver@polysaas.online</a></p>
<p style="color:#94a3b8;font-size:0.85rem;margin:4px 0;text-align:center;">+1-713-913-0434 &nbsp; +63-947-992-7462</p>
</div>'''

# Widget 2: Applications (for footer2/middle-center)
footer2_html = '''<div style="padding:20px 0;">
<h4 style="color:#5eead4;font-size:0.95rem;font-weight:600;margin-bottom:10px;">Applications</h4>
<ul style="list-style:none;padding:0;margin:0;">
<li style="margin-bottom:6px;"><a href="/liferay/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">Liferay</a></li>
<li style="margin-bottom:6px;"><a href="/mattermost/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">MatterMost</a></li>
<li style="margin-bottom:6px;"><a href="/nextcloud/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">NextCloud</a></li>
<li style="margin-bottom:6px;"><a href="/odoo/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">Odoo</a></li>
<li style="margin-bottom:6px;"><a href="/polysysmon/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">PolySysMon</a></li>
<li style="margin-bottom:6px;"><a href="/wordpress/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">WordPress</a></li>
<li style="margin-bottom:6px;"><a href="/dolibarr/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">Dolibarr</a></li>
<li style="margin-bottom:6px;"><a href="/monitor-logger/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">Monitor Logger</a></li>
</ul>
</div>'''

# Widget 3: Features + Gallery (for footer3/middle-right)
footer3_html = '''<div style="padding:20px 0;">
<h4 style="color:#5eead4;font-size:0.95rem;font-weight:600;margin-bottom:10px;">Features</h4>
<ul style="list-style:none;padding:0;margin:0;">
<li style="margin-bottom:6px;"><a href="/bundled-applications/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">Bundled Applications</a></li>
<li style="margin-bottom:6px;"><a href="/external-applications/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">External Applications</a></li>
<li style="margin-bottom:6px;"><a href="/ai-as-peers/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">AI As Peers</a></li>
<li style="margin-bottom:6px;"><a href="/apps-as-peers/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">Apps As Peers</a></li>
<li style="margin-bottom:6px;"><a href="/polysniffer/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">PolySniffer</a></li>
<li style="margin-bottom:6px;"><a href="/dynamic-orchestration/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">Dynamic Orchestration</a></li>
<li style="margin-bottom:6px;"><a href="/atomic-services/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">Atomic Services</a></li>
<li style="margin-bottom:6px;"><a href="/openapi/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">OpenAPI</a></li>
<li style="margin-bottom:6px;"><a href="/portal/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">Portal</a></li>
<li style="margin-bottom:6px;"><a href="/architecture/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">Architecture</a></li>
</ul>
<h4 style="color:#5eead4;font-size:0.95rem;font-weight:600;margin:14px 0 10px;">Gallery</h4>
<ul style="list-style:none;padding:0;margin:0;">
<li style="margin-bottom:6px;"><a href="/gallery-images/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">Images</a></li>
<li style="margin-bottom:6px;"><a href="/gallery-videos/" style="color:#cbd5e1;text-decoration:none;font-size:0.85rem;">Videos</a></li>
</ul>
</div>'''

# Update the existing custom_html widgets and assign to footer sidebars
widgets_config = [
    {"id": "custom_html-2", "sidebar": "footer1", "content": footer1_html},
    {"id": "custom_html-3", "sidebar": "footer2", "content": footer2_html},
    {"id": "custom_html-4", "sidebar": "footer3", "content": footer3_html},
]

for wc in widgets_config:
    # Update widget content and sidebar assignment
    r = s.put(
        f"{AZURE}/wp-json/wp/v2/widgets/{wc['id']}",
        json={
            "id": wc['id'],
            "sidebar": wc['sidebar'],
            "instance": {
                "raw": {
                    "content": wc['content']
                }
            }
        },
        timeout=30
    )
    print(f"Update {wc['id']} -> {wc['sidebar']}: {r.status_code}")
    if r.status_code != 200:
        print(f"  Error: {r.text[:200]}")
        # Try creating fresh
        r2 = s.post(
            f"{AZURE}/wp-json/wp/v2/widgets",
            json={
                "id_base": "custom_html",
                "sidebar": wc['sidebar'],
                "instance": {
                    "raw": {
                        "content": wc['content']
                    }
                }
            },
            timeout=30
        )
        print(f"  Create new: {r2.status_code}")
        if r2.status_code in (200, 201):
            new_id = r2.json().get('id', 'unknown')
            print(f"  New widget ID: {new_id}")
        else:
            print(f"  Error: {r2.text[:200]}")

# Also update the copyright text
print("\n--- Updating copyright ---")
# Check for existing copyright widget
r = s.get(f"{AZURE}/wp-json/wp/v2/sidebars/footer-bottom", timeout=30)
print(f"Footer bottom sidebar: {r.status_code}")

# Verify final state
print("\n=== Final Sidebar State ===")
for sb_id in ['footer1', 'footer2', 'footer3']:
    r = s.get(f"{AZURE}/wp-json/wp/v2/sidebars/{sb_id}", timeout=30)
    if r.status_code == 200:
        data = r.json()
        widgets = data.get('widgets', [])
        print(f"  {sb_id}: {len(widgets)} widget(s) - {[w.get('id', '?') if isinstance(w, dict) else w for w in widgets]}")
    else:
        print(f"  {sb_id}: {r.status_code}")
