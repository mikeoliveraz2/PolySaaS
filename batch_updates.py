"""
Batch updates:
1. Fix pricing page dark mode
2. Upload architecture image + add to Architecture page
3. Upload timeline image + add to About Us Futures Timeline
"""
import requests, re, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# ──────────────────────────────────────────────
# STEP 0: Get all pages and find CSS/toggle donor
# ──────────────────────────────────────────────
pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
}).json()
print(f"Fetched {len(pages)} pages")

page_map = {p['slug']: p for p in pages}

css_blocks = []
toggle_block = ""
for p in pages:
    raw = p['content']['raw']
    for block in re.findall(r'<!-- wp:html -->(.*?)<!-- /wp:html -->', raw, re.DOTALL):
        clean = re.sub(r'</?p>', '', block)
        if '<style' in clean and ('--ps-' in clean or 'body.dark-mode' in clean):
            sig = clean.strip()[:200]
            already = [b.strip()[:200] for b in [re.sub(r'<!-- /?wp:html -->', '', x) for x in css_blocks]]
            if sig not in already:
                css_blocks.append(f"<!-- wp:html -->{clean}<!-- /wp:html -->")
        if ('ps-dark-toggle' in clean or 'ps-theme-toggle' in clean) and not toggle_block:
            toggle_block = f"<!-- wp:html -->{clean}<!-- /wp:html -->"
    if len(css_blocks) >= 2 and toggle_block:
        print(f"Got CSS+toggle from: {p['slug']}")
        break

print(f"CSS blocks: {len(css_blocks)}, Toggle: {'yes' if toggle_block else 'no'}")

# ──────────────────────────────────────────────
# STEP 1: Upload images
# ──────────────────────────────────────────────
def upload_image(filepath, title):
    fname = os.path.basename(filepath)
    with open(filepath, 'rb') as f:
        data = f.read()
    r = s.post(f"{AZURE}/wp-json/wp/v2/media", 
        headers={"Content-Disposition": f'attachment; filename="{title}.png"', "Content-Type": "image/png"},
        data=data)
    if r.status_code == 201:
        j = r.json()
        print(f"Uploaded {title}: id={j['id']} url={j['source_url']}")
        return j['id'], j['source_url']
    else:
        print(f"Upload failed for {title}: {r.status_code} - {r.text[:300]}")
        return None, None

arch_path = r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_Slide3-559be060-67c7-4bc8-be8b-d238411fdfcf.png"
timeline_path = r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\c__Users_PC_AppData_Roaming_Cursor_User_workspaceStorage_77452477b6ce94d3acba53b24d1f01c9_images_Slide4-66ef0e44-6ee5-4d31-8d4a-7683ed85525f.png"

arch_id, arch_url = upload_image(arch_path, "polysaas-architecture-diagram")
timeline_id, timeline_url = upload_image(timeline_path, "polysaas-roadmap-timeline")

# ──────────────────────────────────────────────
# STEP 2: Fix pricing page dark mode
# ──────────────────────────────────────────────
PRICING_HTML = '''<!-- wp:html -->
<div style="max-width:1100px;margin:0 auto;padding:0 20px;">

<div style="text-align:center;margin-bottom:40px;">
<h1 style="color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;margin-bottom:12px;">Pricing Plans</h1>
<p style="color:var(--ps-text,#374151);font-size:1.1rem;max-width:600px;margin:0 auto 12px;line-height:1.6;">Simple, transparent pricing based on the number of applications you choose. Cancel at any time.</p>
<p style="color:var(--ps-muted,#6B7280);font-size:0.9rem;font-style:italic;">Note: WordPress and PolySysMon each count as two applications.</p>
</div>

<div class="ps-pricing-grid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-bottom:40px;">

<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:16px;padding:32px 24px;text-align:center;display:flex;flex-direction:column;">
<h2 style="color:var(--ps-primary,#001F3F);font-size:1.4rem;font-weight:700;margin:0 0 8px;">Starter</h2>
<div style="margin-bottom:16px;">
<span style="color:var(--ps-primary,#001F3F);font-size:2.2rem;font-weight:800;">$29</span>
<span style="color:var(--ps-muted,#6B7280);font-size:0.95rem;">/user/mo</span>
</div>
<p style="color:#2B6CB0;font-weight:600;font-size:1rem;margin:0 0 16px;">Choose 1 application</p>
<ul style="list-style:none;padding:0;margin:0 0 24px;text-align:left;flex-grow:1;">
<li style="padding:8px 0;border-bottom:1px solid var(--ps-border,#e5e7eb);color:var(--ps-text,#374151);font-size:0.92rem;">&#10003; &nbsp;1 from 10 bundled applications</li>
<li style="padding:8px 0;border-bottom:1px solid var(--ps-border,#e5e7eb);color:var(--ps-text,#374151);font-size:0.92rem;">&#10003; &nbsp;or 1 External Application</li>
<li style="padding:8px 0;border-bottom:1px solid var(--ps-border,#e5e7eb);color:var(--ps-text,#374151);font-size:0.92rem;">&#10003; &nbsp;Core PolySaaS features</li>
<li style="padding:8px 0;border-bottom:1px solid var(--ps-border,#e5e7eb);color:var(--ps-text,#374151);font-size:0.92rem;">&#10003; &nbsp;Basic orchestration</li>
<li style="padding:8px 0;color:var(--ps-text,#374151);font-size:0.92rem;">&#10003; &nbsp;Standard support</li>
</ul>
<a href="/sign-up/" style="display:block;background:#2B6CB0;color:#fff;text-align:center;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:0.95rem;">Get Started</a>
</div>

<div style="background:var(--ps-card-bg,#f8fafc);border:2px solid #2B6CB0;border-radius:16px;padding:32px 24px;text-align:center;position:relative;display:flex;flex-direction:column;box-shadow:0 4px 24px rgba(43,108,176,0.15);">
<div style="position:absolute;top:-14px;left:50%;transform:translateX(-50%);background:#2B6CB0;color:#fff;padding:4px 20px;border-radius:20px;font-size:0.75rem;font-weight:700;letter-spacing:0.5px;">MOST POPULAR</div>
<h2 style="color:var(--ps-primary,#001F3F);font-size:1.4rem;font-weight:700;margin:12px 0 8px;">Growth</h2>
<div style="margin-bottom:16px;">
<span style="color:var(--ps-primary,#001F3F);font-size:2.2rem;font-weight:800;">$49</span>
<span style="color:var(--ps-muted,#6B7280);font-size:0.95rem;">/user/mo</span>
</div>
<p style="color:#2B6CB0;font-weight:600;font-size:1rem;margin:0 0 16px;">Choose 3 applications</p>
<ul style="list-style:none;padding:0;margin:0 0 24px;text-align:left;flex-grow:1;">
<li style="padding:8px 0;border-bottom:1px solid var(--ps-border,#e5e7eb);color:var(--ps-text,#374151);font-size:0.92rem;">&#10003; &nbsp;Any combination from bundled &amp; External Applications</li>
<li style="padding:8px 0;border-bottom:1px solid var(--ps-border,#e5e7eb);color:var(--ps-text,#374151);font-size:0.92rem;">&#10003; &nbsp;Everything in Starter</li>
<li style="padding:8px 0;border-bottom:1px solid var(--ps-border,#e5e7eb);color:var(--ps-text,#374151);font-size:0.92rem;">&#10003; &nbsp;Advanced dynamic orchestration</li>
<li style="padding:8px 0;border-bottom:1px solid var(--ps-border,#e5e7eb);color:var(--ps-text,#374151);font-size:0.92rem;">&#10003; &nbsp;AI as Peers</li>
<li style="padding:8px 0;color:var(--ps-text,#374151);font-size:0.92rem;">&#10003; &nbsp;Priority support</li>
</ul>
<a href="/sign-up/" style="display:block;background:#2B6CB0;color:#fff;text-align:center;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:0.95rem;">Get Started</a>
</div>

<div style="background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:16px;padding:32px 24px;text-align:center;display:flex;flex-direction:column;">
<h2 style="color:var(--ps-primary,#001F3F);font-size:1.4rem;font-weight:700;margin:0 0 8px;">Unlimited</h2>
<div style="margin-bottom:16px;">
<span style="color:var(--ps-primary,#001F3F);font-size:2.2rem;font-weight:800;">$99</span>
<span style="color:var(--ps-muted,#6B7280);font-size:0.95rem;">/user/mo</span>
</div>
<p style="color:#2B6CB0;font-weight:600;font-size:1rem;margin:0 0 16px;">Unlimited Applications</p>
<ul style="list-style:none;padding:0;margin:0 0 24px;text-align:left;flex-grow:1;">
<li style="padding:8px 0;border-bottom:1px solid var(--ps-border,#e5e7eb);color:var(--ps-text,#374151);font-size:0.92rem;">&#10003; &nbsp;All bundled + all External Applications</li>
<li style="padding:8px 0;border-bottom:1px solid var(--ps-border,#e5e7eb);color:var(--ps-text,#374151);font-size:0.92rem;">&#10003; &nbsp;Everything in Growth</li>
<li style="padding:8px 0;border-bottom:1px solid var(--ps-border,#e5e7eb);color:var(--ps-text,#374151);font-size:0.92rem;">&#10003; &nbsp;Full PolySniffer &amp; PolySysMon access</li>
<li style="padding:8px 0;border-bottom:1px solid var(--ps-border,#e5e7eb);color:var(--ps-text,#374151);font-size:0.92rem;">&#10003; &nbsp;Custom atomic services on request</li>
<li style="padding:8px 0;color:var(--ps-text,#374151);font-size:0.92rem;">&#10003; &nbsp;Dedicated support + SLA</li>
</ul>
<a href="/sign-up/" style="display:block;background:#2B6CB0;color:#fff;text-align:center;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:0.95rem;">Get Started</a>
</div>

</div>

<div style="text-align:center;max-width:700px;margin:0 auto 20px;">
<p style="color:var(--ps-text,#374151);font-size:0.95rem;line-height:1.6;margin-bottom:8px;">All plans include core PolySaaS features: multi-tenant isolation, GCP hosting, atomic orchestration, and no hidden fees.</p>
<p style="color:var(--ps-muted,#6B7280);font-size:0.9rem;">Annual billing saves 20%. Contact us for enterprise/custom needs.</p>
</div>

<div style="text-align:center;margin:24px 0 40px;">
<a href="/" style="color:#2B6CB0;text-decoration:none;font-size:0.95rem;font-weight:500;">&larr; Back to Home</a>
</div>

</div>

<style>
@media (max-width:768px) {
  .ps-pricing-grid { grid-template-columns: 1fr !important; gap: 20px !important; }
}
</style>
<!-- /wp:html -->'''

pricing = page_map.get('pricing')
if pricing:
    parts = css_blocks + ([toggle_block] if toggle_block else []) + [PRICING_HTML]
    new_content = "\n\n".join(parts)
    r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pricing['id']}", json={"content": new_content})
    print(f"[1] Pricing page: {r.status_code}")
else:
    print("[1] Pricing page not found!")

# ──────────────────────────────────────────────
# STEP 3: Add architecture diagram to Architecture page
# ──────────────────────────────────────────────
arch_page = page_map.get('architecture')
if arch_page and arch_url:
    raw = arch_page['content']['raw']
    # Find the hero section / first content block and inject image after subtitle
    arch_img_block = f'''<!-- wp:html -->
<div style="text-align:center;margin:24px auto 32px;max-width:900px;">
<img src="{arch_url}" alt="PolySaaS Architecture Diagram" style="width:100%;max-width:860px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.12);">
<p style="color:var(--ps-muted,#6B7280);font-size:0.85rem;margin-top:10px;font-style:italic;">PolySaaS multi-tenant architecture &mdash; users access one interface, data flows seamlessly between SaaS applications</p>
</div>
<!-- /wp:html -->'''
    # Insert after subtitle (look for first closing h2 or subtitle paragraph)
    # Strategy: insert after the hero/subtitle block
    if 'Key Capabilities' in raw:
        insertion = raw.find('Key Capabilities')
        # go back to find the wp:html boundary before it
        prev_end = raw.rfind('<!-- wp:html -->', 0, insertion)
        if prev_end > 0:
            new_raw = raw[:prev_end] + arch_img_block + "\n\n" + raw[prev_end:]
        else:
            # fallback: insert after first wp:html block
            first_end = raw.find('<!-- /wp:html -->') + len('<!-- /wp:html -->')
            new_raw = raw[:first_end] + "\n\n" + arch_img_block + "\n\n" + raw[first_end:]
    else:
        first_end = raw.find('<!-- /wp:html -->') + len('<!-- /wp:html -->')
        new_raw = raw[:first_end] + "\n\n" + arch_img_block + "\n\n" + raw[first_end:]
    
    r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{arch_page['id']}", json={"content": new_raw})
    print(f"[2] Architecture page: {r.status_code}")
elif not arch_url:
    print("[2] Architecture image upload failed, skipping page update")
else:
    print("[2] Architecture page not found!")

# ──────────────────────────────────────────────
# STEP 4: Add timeline image to About Us page
# ──────────────────────────────────────────────
about_page = page_map.get('about-us') or page_map.get('about')
if not about_page:
    for p in pages:
        if 'about' in p['slug']:
            about_page = p
            break

if about_page and timeline_url:
    raw = about_page['content']['raw']
    timeline_img_block = f'''<!-- wp:html -->
<div style="text-align:center;margin:20px auto 32px;max-width:900px;">
<img src="{timeline_url}" alt="PolySaaS Roadmap Timeline" style="width:100%;max-width:860px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.12);">
<p style="color:var(--ps-muted,#6B7280);font-size:0.85rem;margin-top:10px;font-style:italic;">PolySaaS 2025 Roadmap &mdash; Q1 through Q4 milestones</p>
</div>
<!-- /wp:html -->'''
    
    # Find the Futures Timeline heading and insert the image after it
    if 'Futures Timeline' in raw:
        idx = raw.find('Futures Timeline')
        # Find the end of the wp:html block containing the heading
        block_end = raw.find('<!-- /wp:html -->', idx)
        if block_end > 0:
            insert_pos = block_end + len('<!-- /wp:html -->')
            new_raw = raw[:insert_pos] + "\n\n" + timeline_img_block + "\n\n" + raw[insert_pos:]
        else:
            new_raw = raw + "\n\n" + timeline_img_block
    else:
        # Append at the end before any final CTA
        new_raw = raw + "\n\n" + timeline_img_block
    
    r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{about_page['id']}", json={"content": new_raw})
    print(f"[3] About Us page (slug={about_page['slug']}, id={about_page['id']}): {r.status_code}")
elif not timeline_url:
    print("[3] Timeline image upload failed, skipping page update")
else:
    print("[3] About Us page not found!")

print("\nAll done.")
