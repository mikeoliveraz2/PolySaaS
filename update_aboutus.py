"""
Update About Us page:
1. Replace old timeline (Q1 2025-based) with corrected Q1-Q4 2026 timeline
2. Add Scott Chate's headshot to advisors section
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

SCOTT_URL = "https://azure-nightingale-589250.hostingersite.com/wp-content/uploads/2026/03/scott-chate-headshot.jpg"

pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "about-us", "context": "edit", "_fields": "id,content"
}).json()
about = pages[0]
raw = about['content']['raw']

# --- PART 1: Replace timeline ---
# Find start: the div containing "Futures Timeline" heading
# The timeline section starts with the container div before the h2
tl_h2_idx = raw.find('Futures Timeline')
if tl_h2_idx < 0:
    print("ERROR: Cannot find 'Futures Timeline'")
    sys.exit(1)

# Go back to find the containing div
search_back = raw[:tl_h2_idx]
container_start = search_back.rfind('<div style="max-width:800px')
if container_start < 0:
    container_start = search_back.rfind('<div style="max-width:')
print(f"Timeline container starts at: {container_start}")

# Find the end: the timeline ends with closing divs before the roadmap image block
# The roadmap image is in a wp:html block
roadmap_block_start = raw.find('<!-- wp:html -->', tl_h2_idx)
if roadmap_block_start < 0:
    # No roadmap block after timeline, find end by closing divs
    roadmap_block_start = len(raw)

# The timeline HTML ends with </div></div> before the next section
# Count from tl_h2_idx forward to find the end of the timeline div structure
# The timeline has a wrapper div (max-width:800px) containing everything
# We need to find its closing </div>
# Strategy: find all </div> after the container and match nesting
depth = 0
pos = container_start
end_pos = None
i = container_start
while i < roadmap_block_start:
    if raw[i:i+4] == '<div':
        depth += 1
        i += 4
    elif raw[i:i+6] == '</div>':
        depth -= 1
        if depth == 0:
            end_pos = i + 6
            break
        i += 6
    else:
        i += 1

if end_pos is None:
    print("ERROR: Cannot find end of timeline section")
    sys.exit(1)

old_timeline = raw[container_start:end_pos]
print(f"Old timeline: {len(old_timeline)} chars (pos {container_start}-{end_pos})")
print(f"  Starts with: {old_timeline[:100]}")
print(f"  Ends with: {old_timeline[-100:]}")

NEW_TIMELINE = '''<div style="max-width:800px;margin:40px auto;padding:0 20px;">
<h2 style="text-align:center;color:var(--ps-primary,#001F3F);font-size:1.8rem;font-weight:700;margin-bottom:32px;">Futures Timeline</h2>
<div style="position:relative;padding-left:40px;">
<div style="position:absolute;left:15px;top:0;bottom:0;width:3px;background:linear-gradient(to bottom, #2B6CB0, #0F766E, #60A5FA, #8B5CF6);border-radius:2px;"></div>

<div style="position:relative;margin-bottom:36px;">
<div style="position:absolute;left:-33px;top:4px;width:14px;height:14px;background:#2B6CB0;border:3px solid var(--ps-bg,#fff);border-radius:50%;box-shadow:0 0 0 3px #2B6CB0;"></div>
<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:20px;">
<span style="display:inline-block;background:#2B6CB0;color:#fff;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;margin-bottom:8px;">Q1 2026 &mdash; In Progress</span>
<h3 style="color:var(--ps-primary,#001F3F);margin:8px 0 6px;font-size:1.15rem;">Platform Foundation &amp; GCP Deployment</h3>
<ul style="color:var(--ps-text,#1F2937);margin:0;padding-left:18px;line-height:1.8;font-size:0.95rem;">
<li><strong>Dynamic Orchestration</strong> &mdash; <span style="color:#0F766E;font-weight:600;">Complete</span></li>
<li><strong>GCP Deployment</strong> &mdash; Production infrastructure rollout</li>
<li><strong>AI As Peers</strong> &mdash; AI agents collaborating as team members</li>
<li><strong>All Bundled Apps</strong> &mdash; Full suite operational</li>
<li><strong>Google Cloud Startup Application</strong> &mdash; <span style="color:#D97706;font-weight:600;">Pending</span></li>
<li><strong>User Guide</strong> &mdash; Documentation for onboarding</li>
</ul>
</div></div>

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

<div style="position:relative;margin-bottom:36px;">
<div style="position:absolute;left:-33px;top:4px;width:14px;height:14px;background:#8B5CF6;border:3px solid var(--ps-bg,#fff);border-radius:50%;box-shadow:0 0 0 3px #8B5CF6;"></div>
<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:12px;padding:20px;">
<span style="display:inline-block;background:#8B5CF6;color:#fff;padding:3px 12px;border-radius:20px;font-size:0.75rem;font-weight:600;margin-bottom:8px;">Q4 2026 &mdash; Vision</span>
<h3 style="color:var(--ps-primary,#001F3F);margin:8px 0 6px;font-size:1.15rem;">Enterprise Maturity &amp; Expansion</h3>
<p style="color:var(--ps-text,#1F2937);margin:0;line-height:1.6;font-size:0.95rem;">Marketplace launch, enterprise features including SSO and compliance, full GCP production scaling, and external connector ecosystem. Details to be confirmed.</p>
</div></div>

</div></div>'''

new_raw = raw[:container_start] + NEW_TIMELINE + raw[end_pos:]
print(f"\nReplaced timeline. Old: {len(raw)} chars -> New: {len(new_raw)} chars")

# --- PART 2: Add Scott's headshot ---
# Find Scott Chate in the advisors section
scott_idx = new_raw.find('Scott Chate')
if scott_idx > 0:
    print(f"\nFound 'Scott Chate' at {scott_idx}")
    # Check if there's already an img near Scott
    scott_area = new_raw[max(0,scott_idx-500):scott_idx+200]
    if 'scott-chate-headshot' in scott_area:
        print("  Scott already has headshot - skipping")
    else:
        # Find the advisor card div containing Scott
        # Look for the img placeholder or icon before his name
        card_start = new_raw.rfind('<div style="', max(0,scott_idx-400), scott_idx)
        # Find the placeholder icon/image for Scott
        # Look for a generic advisor image or icon before his name
        placeholder = new_raw.rfind('<div style="width:', max(0,scott_idx-300), scott_idx)
        if placeholder < 0:
            placeholder = new_raw.rfind('<img', max(0,scott_idx-300), scott_idx)
        
        if placeholder > 0:
            # Find the end of the current image/placeholder element
            placeholder_end = new_raw.find('>', placeholder) + 1
            if new_raw[placeholder:placeholder+4] == '<div':
                # It's a div placeholder, find its closing
                depth2 = 0
                j = placeholder
                while j < scott_idx:
                    if new_raw[j:j+4] == '<div':
                        depth2 += 1
                        j += 4
                    elif new_raw[j:j+6] == '</div>':
                        depth2 -= 1
                        if depth2 == 0:
                            placeholder_end = j + 6
                            break
                        j += 6
                    else:
                        j += 1
            
            scott_img = f'<img src="{SCOTT_URL}" alt="Scott Chate" style="width:100px;height:100px;border-radius:50%;object-fit:cover;">'
            old_placeholder = new_raw[placeholder:placeholder_end]
            print(f"  Replacing placeholder ({len(old_placeholder)} chars): {old_placeholder[:100]}...")
            new_raw = new_raw[:placeholder] + scott_img + new_raw[placeholder_end:]
            print("  Added Scott's headshot")
        else:
            print("  Could not find placeholder before Scott's name")
            # Insert headshot right before his name
            name_div = new_raw.rfind('<h', max(0,scott_idx-100), scott_idx)
            if name_div < 0:
                name_div = scott_idx
            scott_img = f'<div style="text-align:center;margin-bottom:8px;"><img src="{SCOTT_URL}" alt="Scott Chate" style="width:100px;height:100px;border-radius:50%;object-fit:cover;"></div>'
            new_raw = new_raw[:name_div] + scott_img + new_raw[name_div:]
            print("  Inserted headshot before name")
else:
    print("\nScott Chate not found on About Us page!")

# Save
r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{about['id']}", json={"content": new_raw})
print(f"\nUpdate About Us: {r.status_code}")
if r.status_code == 200:
    print("Done! Timeline corrected + Scott headshot added")
else:
    print(f"Error: {r.text[:300]}")
