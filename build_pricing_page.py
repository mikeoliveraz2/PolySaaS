"""
Build the Pricing page on Azure staging, matching production content
with the same design system (dark mode, toggle, etc.) used on all other pages.
"""
import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get homepage to extract CSS / toggle blocks
hp = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "slug": "home-3", "context": "edit", "_fields": "id,content"
}).json()
if not hp:
    hp = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
        "per_page": 100, "context": "edit", "_fields": "id,slug,content"
    }).json()
    hp = [p for p in hp if p['slug'] in ('home-3', 'home')]
    if hp:
        hp = hp[0]
    else:
        print("Cannot find homepage!")
        sys.exit(1)
else:
    hp = hp[0]

hp_raw = hp['content']['raw']

# Extract CSS blocks (style tags inside wp:html)
css_blocks = []
toggle_block = ""
for block in re.findall(r'<!-- wp:html -->(.*?)<!-- /wp:html -->', hp_raw, re.DOTALL):
    if '<style' in block and ('--ps-' in block or 'body.dark-mode' in block or '.ps-' in block):
        clean = re.sub(r'</?p>', '', block)
        css_blocks.append(f"<!-- wp:html -->{clean}<!-- /wp:html -->")
    if 'ps-dark-toggle' in block or 'ps-theme-toggle' in block:
        clean = re.sub(r'</?p>', '', block)
        toggle_block = f"<!-- wp:html -->{clean}<!-- /wp:html -->"

print(f"Extracted {len(css_blocks)} CSS blocks, toggle: {'yes' if toggle_block else 'no'}")

PRICING_HTML = '''<!-- wp:html -->
<div style="max-width:1100px;margin:0 auto;padding:0 20px;">

<div style="text-align:center;margin-bottom:40px;">
<h1 style="color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;margin-bottom:12px;">Pricing Plans</h1>
<p style="color:var(--ps-text,#374151);font-size:1.1rem;max-width:600px;margin:0 auto 12px;line-height:1.6;">Simple, transparent pricing based on the number of applications you choose. Cancel at any time.</p>
<p style="color:var(--ps-muted,#6B7280);font-size:0.9rem;font-style:italic;">Note: WordPress and PolySysMon each count as two applications.</p>
</div>

<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-bottom:40px;">

<!-- Starter -->
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
<a href="/sign-up/" style="display:block;background:#2B6CB0;color:#fff;text-align:center;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:0.95rem;transition:background 0.2s;">Get Started</a>
</div>

<!-- Growth (Most Popular) -->
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
<a href="/sign-up/" style="display:block;background:#2B6CB0;color:#fff;text-align:center;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:0.95rem;transition:background 0.2s;">Get Started</a>
</div>

<!-- Unlimited -->
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
<a href="/sign-up/" style="display:block;background:#2B6CB0;color:#fff;text-align:center;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:0.95rem;transition:background 0.2s;">Get Started</a>
</div>

</div>

<div style="max-width:760px;margin:0 auto 32px;background:var(--ps-card-bg,#f8fafc);border:1px solid var(--ps-border,#e5e7eb);border-radius:16px;padding:28px 28px 24px;box-shadow:0 4px 16px rgba(15,23,42,0.04);">
<h2 style="color:var(--ps-primary,#001F3F);font-size:1.45rem;font-weight:700;margin:0 0 14px;text-align:center;">Additional Users Per Tenant</h2>
<ul style="margin:0;padding-left:20px;color:var(--ps-text,#374151);font-size:0.97rem;line-height:1.75;">
<li><strong>Users 2-10</strong> - Each user gets a discount of 10%</li>
<li><strong>Users 11-20</strong> - Each user gets a discount of 20%</li>
<li><strong>Users 31+</strong> - Each user gets a discount of 30%</li>
</ul>
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
  div[style*="grid-template-columns:repeat(3"] {
    grid-template-columns: 1fr !important;
    gap: 20px !important;
  }
}
</style>
<!-- /wp:html -->'''

# Build full page content
parts = []
for cb in css_blocks:
    parts.append(cb)
if toggle_block:
    parts.append(toggle_block)
parts.append(PRICING_HTML)

new_content = "\n\n".join(parts)

# Update pricing page (id=1349)
r = s.post(f"{AZURE}/wp-json/wp/v2/pages/1349", json={
    "content": new_content
})
print(f"Update pricing page: {r.status_code}")
if r.status_code == 200:
    print("Pricing page updated successfully!")
else:
    print(f"Error: {r.text[:500]}")
