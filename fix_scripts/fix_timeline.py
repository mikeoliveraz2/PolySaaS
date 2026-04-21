"""
Update the Futures Timeline on the About Us page.
- Q1 2026: GCP Deployment, AI As Peers, All Bundled Apps, User Guide
- Q2 2026: Marketing launch, Apps As Peers, Developer Guide, Django Examples, Liferay Examples, White Label Version
- Q3 2026: Shared Annotations, Mobile App Version
- Q4 2026: TBD / Expansion phase
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
}).json()

about = [p for p in pages if p['slug'] == 'about-us'][0]
raw = about['content']['raw']

# Find the existing Futures Timeline section
# It starts with "Futures Timeline" heading and goes to the end of that wp:html block
# Let me check what's there
blocks = re.findall(r'(<!-- wp:html -->.*?<!-- /wp:html -->)', raw, re.DOTALL)
timeline_idx = None
for i, b in enumerate(blocks):
    if 'Futures Timeline' in b:
        timeline_idx = i
        print(f"Found Futures Timeline in block {i} ({len(b)} chars)")
        break

if timeline_idx is None:
    print("Futures Timeline block not found!")
    sys.exit(1)

NEW_TIMELINE = '''<!-- wp:html -->
<div style="max-width:800px;margin:40px auto;padding:0 20px;">
<h2 style="text-align:center;color:var(--ps-primary,#001F3F);font-size:1.8rem;font-weight:700;margin-bottom:32px;">Futures Timeline</h2>
<div style="position:relative;padding-left:40px;">
<div style="position:absolute;left:15px;top:0;bottom:0;width:3px;background:linear-gradient(to bottom, #2B6CB0, #0F766E, #60A5FA, #8B5CF6);border-radius:2px;"></div>

<!-- Q1 2026 -->
<div style="position:relative;margin-bottom:36px;">
<div style="position:absolute;left:-33px;top:4px;width:14px;height:14px;background:#2B6CB0;border:3px solid var(--ps-bg,#fff);border-radius:50%;box-shadow:0 0 0 3px #2B6CB0;"></div>
<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:20px;">
<span style="display:inline-block;background:#2B6CB0;color:#fff;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;margin-bottom:8px;">Q1 2026 &mdash; In Progress</span>
<h3 style="color:var(--ps-primary,#001F3F);margin:8px 0 6px;font-size:1.15rem;">Platform Foundation &amp; GCP Deployment</h3>
<ul style="color:var(--ps-text,#1F2937);margin:0;padding-left:18px;line-height:1.8;font-size:0.95rem;">
<li><strong>Dynamic Orchestration</strong> &mdash; <span style="color:#0F766E;font-weight:600;">Complete</span></li>
<li><strong>GCP Deployment</strong> &mdash; Production infrastructure rollout</li>
<li><strong>AI As Peers</strong> &mdash; AI agents collaborating as team members</li>
<li><strong>All Bundled Apps</strong> &mdash; Full suite operational (Odoo, Nextcloud, Mattermost, WordPress, Liferay, Dolibarr, Monitor Logger, PolySysMon)</li>
<li><strong>Google Cloud Startup Application</strong> &mdash; <span style="color:#D97706;font-weight:600;">Pending</span></li>
<li><strong>User Guide</strong> &mdash; Documentation for onboarding</li>
</ul>
</div></div>

<!-- Q2 2026 -->
<div style="position:relative;margin-bottom:36px;">
<div style="position:absolute;left:-33px;top:4px;width:14px;height:14px;background:#0F766E;border:3px solid var(--ps-bg,#fff);border-radius:50%;box-shadow:0 0 0 3px #0F766E;"></div>
<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:20px;">
<span style="display:inline-block;background:#0F766E;color:#fff;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;margin-bottom:8px;">Q2 2026 &mdash; Upcoming</span>
<h3 style="color:var(--ps-primary,#001F3F);margin:8px 0 6px;font-size:1.15rem;">Marketing Launch &amp; Integration Expansion</h3>
<ul style="color:var(--ps-text,#1F2937);margin:0;padding-left:18px;line-height:1.8;font-size:0.95rem;">
<li><strong>Marketing Campaign Launch</strong> &mdash; Full go-to-market</li>
<li><strong>Apps As Peers</strong> &mdash; Applications communicating directly via Atomic Services</li>
<li><strong>Developer Guide</strong> &mdash; Django and Liferay examples</li>
<li><strong>White Label Version</strong> &mdash; Custom branding for partners and resellers</li>
</ul>
</div></div>

<!-- Q3 2026 -->
<div style="position:relative;margin-bottom:36px;">
<div style="position:absolute;left:-33px;top:4px;width:14px;height:14px;background:#60A5FA;border:3px solid var(--ps-bg,#fff);border-radius:50%;box-shadow:0 0 0 3px #60A5FA;"></div>
<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:20px;">
<span style="display:inline-block;background:#60A5FA;color:#fff;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;margin-bottom:8px;">Q3 2026 &mdash; Planned</span>
<h3 style="color:var(--ps-primary,#001F3F);margin:8px 0 6px;font-size:1.15rem;">Collaboration &amp; Mobile</h3>
<ul style="color:var(--ps-text,#1F2937);margin:0;padding-left:18px;line-height:1.8;font-size:0.95rem;">
<li><strong>Shared Annotations</strong> &mdash; Collaborative notes and edits across apps and users</li>
<li><strong>Mobile App Version</strong> &mdash; Native or progressive web app access</li>
</ul>
</div></div>

<!-- Q4 2026 -->
<div style="position:relative;margin-bottom:36px;">
<div style="position:absolute;left:-33px;top:4px;width:14px;height:14px;background:#8B5CF6;border:3px solid var(--ps-bg,#fff);border-radius:50%;box-shadow:0 0 0 3px #8B5CF6;"></div>
<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:20px;">
<span style="display:inline-block;background:#8B5CF6;color:#fff;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;margin-bottom:8px;">Q4 2026 &mdash; Vision</span>
<h3 style="color:var(--ps-primary,#001F3F);margin:8px 0 6px;font-size:1.15rem;">Enterprise Maturity &amp; Expansion</h3>
<p style="color:var(--ps-text,#1F2937);margin:0;line-height:1.6;font-size:0.95rem;">Marketplace launch, enterprise features including SSO and compliance, full GCP production scaling, and external connector ecosystem. Details to be confirmed.</p>
</div></div>

</div></div>
<!-- /wp:html -->'''

# Replace the old timeline block with the new one
old_block = blocks[timeline_idx]
new_raw = raw.replace(old_block, NEW_TIMELINE)

r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{about['id']}", json={"content": new_raw})
print(f"Update About Us: {r.status_code}")
if r.status_code == 200:
    print("Timeline updated: Q1=GCP+foundation, Q2=Marketing+integration, Q3=Collab+mobile, Q4=Enterprise/TBD")
