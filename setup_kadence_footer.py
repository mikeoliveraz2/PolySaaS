"""Set up Kadence footer widgets with the standard footer content."""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Footer content split into 3 widget areas + bottom bar

# Footer 1: CTA + Contact Info
footer1_html = '''<div style="padding:20px 0;">
<h3 style="color:#5eead4;font-size:1.1rem;font-weight:600;margin-bottom:4px;text-align:center;">Stop Managing Tools. Start Orchestrating Them.</h3>
<p style="color:#ccc;text-align:center;font-size:0.9rem;margin-bottom:12px;">Join enterprises already running smarter with PolySaaS.</p>
<div style="text-align:center;margin-bottom:20px;">
<a href="/schedule-demo/" style="display:inline-block;padding:10px 28px;background:linear-gradient(135deg,#5eead4,#2dd4bf);color:#0f172a;border-radius:8px;text-decoration:none;font-weight:600;font-size:0.95rem;">Sign Up for a Demo</a>
</div>
<div style="color:#ccc;font-size:0.85rem;line-height:1.7;">
<p style="margin:0;">5900 Balcones Drive Suite 100<br>Austin, TX 78731</p>
<p style="margin:8px 0 0;"><a href="mailto:michael.oliver@polysaas.online" style="color:#5eead4;text-decoration:none;">michael.oliver@polysaas.online</a></p>
<p style="margin:4px 0 0;">+1-713-913-0434<br>+63-947-992-7462</p>
</div>
</div>'''

# Footer 2: Applications
footer2_html = '''<div style="padding:20px 0;">
<h4 style="color:#5eead4;font-size:16px;margin-bottom:8px;font-weight:600;">Applications</h4>
<a href="/liferay-2/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">Liferay</a>
<a href="/mattermost/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">MatterMost</a>
<a href="/nextcloud/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">NextCloud</a>
<a href="/odoo/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">Odoo</a>
<a href="/polysysmon/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">PolySysMon</a>
<a href="/wordpress-3/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">WordPress</a>
<a href="/dolibarr-3/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">Dolibarr</a>
<a href="/monitor-logger-4/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">Monitor Logger</a>
</div>'''

# Footer 3: Features + Gallery
footer3_html = '''<div style="padding:20px 0;">
<h4 style="color:#5eead4;font-size:16px;margin-bottom:8px;font-weight:600;">Features</h4>
<a href="/bundled-applications/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">Bundled Applications</a>
<a href="/ai-as-peers/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">AI As Peers</a>
<a href="/apps-as-peers/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">Apps As Peers</a>
<a href="/polysniffer/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">PolySniffer</a>
<a href="/dynamic-orchestration/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">Dynamic Orchestration</a>
<a href="/atomic-services/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">Atomic Services</a>
<a href="/openapi-2/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">OpenAPI</a>
<a href="/portal/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">Portal</a>
<a href="/architecture/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">Architecture</a>
<h4 style="color:#5eead4;font-size:16px;margin:16px 0 8px;font-weight:600;">Gallery</h4>
<a href="/gallery-images/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">Images</a>
<a href="/gallery-videos/" style="color:#ccc;text-decoration:none;display:block;margin:3px 0;">Videos</a>
</div>'''

# Add widgets to footer areas
widgets = [
    ("footer1", footer1_html, "Footer - Contact & CTA"),
    ("footer2", footer2_html, "Footer - Applications"),
    ("footer3", footer3_html, "Footer - Features & Gallery"),
]

for sidebar_id, html_content, title in widgets:
    # Create a Custom HTML widget in the sidebar
    payload = {
        "sidebar": sidebar_id,
        "id_base": "custom_html",
        "instance": {
            "raw": {
                "title": "",
                "content": html_content,
            }
        }
    }
    
    r = s.post(f"{AZURE}/wp-json/wp/v2/widgets", json=payload)
    if r.status_code == 201:
        widget = r.json()
        print(f"  OK  {sidebar_id}: {title} (widget ID: {widget['id']})")
    else:
        print(f"  ERR {sidebar_id}: {r.status_code} {r.text[:200]}")

print("\nWidgets created. Now need to configure Kadence footer builder via Customizer.")
