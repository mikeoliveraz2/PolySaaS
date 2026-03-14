"""
Replace the feature showcase section (Apps As Peers, OpenAPI, AI As Peers)
on the About Us page with a Futures Timeline.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from wp_snapshot import take_snapshot
take_snapshot("before replacing about-us features with timeline")

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
})
pages = {p['slug']: p for p in r.json()}
about = pages['about-us']
raw = about['content']['raw']

# The feature section starts with the footer-like columns block with "Apps As Peers"
# and ends just before the "Stop Managing Tools" CTA banner.
# 
# Start marker: the columns block containing "Apps As Peers" heading
# End marker: the "Stop Managing Tools" CTA banner

# Find the start of the feature showcase section
# It starts after the "Get in Touch" CTA closing divs, at the footer-like columns
start_marker = '<div class="wp-block-columns are-vertically-aligned-center is-layout-flex wp-container-core-columns-is-layout-8230ba40'
end_marker = '<div class="wp-block-group ps-cta-banner"'

start_idx = raw.find(start_marker)
end_idx = raw.find(end_marker)

if start_idx == -1:
    print("ERROR: Could not find start of feature section")
    # Try alternative approach - find by content
    start_idx = raw.find('Apps As Peers</h3>')
    if start_idx != -1:
        # Walk backwards to find the enclosing div
        temp = raw[:start_idx]
        # Find the wp-block-columns div before this
        last_columns = temp.rfind('<div class="wp-block-columns')
        if last_columns != -1:
            start_idx = last_columns
            print(f"Found feature section start via content at position {start_idx}")

if end_idx == -1:
    print("ERROR: Could not find end of feature section")
    end_idx = raw.find('Stop Managing Tools')
    if end_idx != -1:
        temp = raw[:end_idx]
        last_div = temp.rfind('<div class="wp-block-group')
        if last_div != -1:
            end_idx = last_div
            print(f"Found feature section end via content at position {end_idx}")

if start_idx == -1 or end_idx == -1:
    print("FATAL: Could not locate feature section boundaries")
    sys.exit(1)

print(f"Feature section: chars {start_idx} to {end_idx}")
old_section = raw[start_idx:end_idx]
print(f"Section length: {len(old_section)} chars")

# Preview what we're replacing
text_preview = re.sub(r'<[^>]+>', ' ', old_section)
text_preview = re.sub(r'\s+', ' ', text_preview).strip()
print(f"Text preview: {text_preview[:300]}...")

# Build the Futures Timeline
TIMELINE_HTML = '''
<div style="max-width:800px;margin:40px auto;padding:0 20px;">
<h2 style="text-align:center;color:var(--ps-primary,#001F3F);font-size:1.8rem;font-weight:700;margin-bottom:32px;">Futures Timeline</h2>

<div style="position:relative;padding-left:40px;">
<!-- Vertical line -->
<div style="position:absolute;left:15px;top:0;bottom:0;width:3px;background:linear-gradient(to bottom, #2B6CB0, #0F766E, #60A5FA);border-radius:2px;"></div>

<!-- Q1 2025 -->
<div style="position:relative;margin-bottom:36px;">
<div style="position:absolute;left:-33px;top:4px;width:14px;height:14px;background:#0F766E;border:3px solid var(--ps-bg,#fff);border-radius:50%;box-shadow:0 0 0 3px #0F766E;"></div>
<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:20px;">
<span style="display:inline-block;background:#0F766E;color:#fff;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;margin-bottom:8px;">Q1 2025 &mdash; Completed</span>
<h3 style="color:var(--ps-primary,#001F3F);margin:8px 0 6px;font-size:1.15rem;">Platform Foundation</h3>
<p style="color:var(--ps-text,#1F2937);margin:0;line-height:1.6;font-size:0.95rem;">Core Django/DOSE framework established. Multi-tenant architecture designed. Initial Liferay portal and Mattermost integration. PolySniffer prototype for passive traffic analysis.</p>
</div>
</div>

<!-- Q3 2025 -->
<div style="position:relative;margin-bottom:36px;">
<div style="position:absolute;left:-33px;top:4px;width:14px;height:14px;background:#0F766E;border:3px solid var(--ps-bg,#fff);border-radius:50%;box-shadow:0 0 0 3px #0F766E;"></div>
<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:20px;">
<span style="display:inline-block;background:#0F766E;color:#fff;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;margin-bottom:8px;">Q3 2025 &mdash; Completed</span>
<h3 style="color:var(--ps-primary,#001F3F);margin:8px 0 6px;font-size:1.15rem;">Bundled Applications Suite</h3>
<p style="color:var(--ps-text,#1F2937);margin:0;line-height:1.6;font-size:0.95rem;">Eight enterprise-grade applications bundled: Odoo, Nextcloud, Mattermost, WordPress, Liferay, Dolibarr, Monitor Logger, and PolySysMon. Docker containerization for consistent deployment.</p>
</div>
</div>

<!-- Q1 2026 -->
<div style="position:relative;margin-bottom:36px;">
<div style="position:absolute;left:-33px;top:4px;width:14px;height:14px;background:#2B6CB0;border:3px solid var(--ps-bg,#fff);border-radius:50%;box-shadow:0 0 0 3px #2B6CB0;"></div>
<div style="background:var(--ps-card-bg,#f8fafc);border:2px solid #2B6CB0;border-radius:12px;padding:20px;">
<span style="display:inline-block;background:#2B6CB0;color:#fff;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;margin-bottom:8px;">Q1 2026 &mdash; In Progress</span>
<h3 style="color:var(--ps-primary,#001F3F);margin:8px 0 6px;font-size:1.15rem;">Apps As Peers &amp; AI Integration</h3>
<p style="color:var(--ps-text,#1F2937);margin:0;line-height:1.6;font-size:0.95rem;">Standardized peer-to-peer communication between all bundled applications via Atomic Services. AI As Peers brings intelligent agents into Mattermost workflows. OpenAPI/Swagger documentation for all endpoints.</p>
</div>
</div>

<!-- Q2 2026 -->
<div style="position:relative;margin-bottom:36px;">
<div style="position:absolute;left:-33px;top:4px;width:14px;height:14px;background:#60A5FA;border:3px solid var(--ps-bg,#fff);border-radius:50%;box-shadow:0 0 0 3px #60A5FA;"></div>
<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:20px;">
<span style="display:inline-block;background:#60A5FA;color:#fff;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;margin-bottom:8px;">Q2 2026 &mdash; Upcoming</span>
<h3 style="color:var(--ps-primary,#001F3F);margin:8px 0 6px;font-size:1.15rem;">Dynamic Orchestration Engine</h3>
<p style="color:var(--ps-text,#1F2937);margin:0;line-height:1.6;font-size:0.95rem;">Visual workflow builder for no-code automation across all bundled applications. Event-driven triggers, conditional logic, and runtime customization without redeployment.</p>
</div>
</div>

<!-- Q3 2026 -->
<div style="position:relative;margin-bottom:36px;">
<div style="position:absolute;left:-33px;top:4px;width:14px;height:14px;background:#60A5FA;border:3px solid var(--ps-bg,#fff);border-radius:50%;box-shadow:0 0 0 3px #60A5FA;"></div>
<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:20px;">
<span style="display:inline-block;background:#60A5FA;color:#fff;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;margin-bottom:8px;">Q3 2026 &mdash; Upcoming</span>
<h3 style="color:var(--ps-primary,#001F3F);margin:8px 0 6px;font-size:1.15rem;">GCP Production &amp; Kubernetes</h3>
<p style="color:var(--ps-text,#1F2937);margin:0;line-height:1.6;font-size:0.95rem;">Full production deployment on Google Cloud Platform with GKE. Auto-scaling, rolling updates, and self-healing. Multi-region availability for enterprise clients.</p>
</div>
</div>

<!-- Q4 2026 -->
<div style="position:relative;margin-bottom:36px;">
<div style="position:absolute;left:-33px;top:4px;width:14px;height:14px;background:#94A3B8;border:3px solid var(--ps-bg,#fff);border-radius:50%;box-shadow:0 0 0 3px #94A3B8;"></div>
<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:20px;">
<span style="display:inline-block;background:#94A3B8;color:#fff;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;margin-bottom:8px;">Q4 2026 &mdash; Planned</span>
<h3 style="color:var(--ps-primary,#001F3F);margin:8px 0 6px;font-size:1.15rem;">Marketplace &amp; Partner Ecosystem</h3>
<p style="color:var(--ps-text,#1F2937);margin:0;line-height:1.6;font-size:0.95rem;">Launch partner marketplace for Liferay resellers and Django integrators. White-label portal branding. External application connectors allowing third-party SaaS to join the PolySaaS ecosystem.</p>
</div>
</div>

<!-- 2027 -->
<div style="position:relative;margin-bottom:16px;">
<div style="position:absolute;left:-33px;top:4px;width:14px;height:14px;background:#94A3B8;border:3px solid var(--ps-bg,#fff);border-radius:50%;box-shadow:0 0 0 3px #94A3B8;"></div>
<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:20px;">
<span style="display:inline-block;background:#94A3B8;color:#fff;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;margin-bottom:8px;">2027 &mdash; Vision</span>
<h3 style="color:var(--ps-primary,#001F3F);margin:8px 0 6px;font-size:1.15rem;">Enterprise Scale &amp; Global Reach</h3>
<p style="color:var(--ps-text,#1F2937);margin:0;line-height:1.6;font-size:0.95rem;">Full enterprise feature parity: SSO federation, advanced compliance (SOC 2, HIPAA), CI/CD pipeline annotations, and multi-region tenant isolation. Target: 10x scaling capability supporting billions of orchestration events.</p>
</div>
</div>

</div>
</div>
'''

# Replace the feature section with the timeline
new_raw = raw[:start_idx] + TIMELINE_HTML + '\n' + raw[end_idx:]

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{about['id']}", json={"content": new_raw})
if r2.status_code == 200:
    print("SUCCESS: About Us page updated with Futures Timeline")
else:
    print(f"FAILED: {r2.status_code}")
    print(r2.text[:500])
