"""
Rebuild pricing page with CSS, toggle, and pricing content.
"""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get CSS + toggle from a known good page
pages = s.get(f"{AZURE}/wp-json/wp/v2/pages", params={
    "per_page": 100, "context": "edit", "_fields": "id,slug,content"
}).json()

css_blocks = []
toggle_block = ""

for p in pages:
    raw = p['content']['raw']
    for block in re.findall(r'<!-- wp:html -->(.*?)<!-- /wp:html -->', raw, re.DOTALL):
        clean = re.sub(r'</?p>', '', block)
        if '<style' in clean and ('--ps-' in clean or 'body.dark-mode' in clean):
            sig = clean.strip()[:200]
            if sig not in [b[:200] for b in [re.sub(r'</?p>', '', x.replace('<!-- wp:html -->','').replace('<!-- /wp:html -->','')) for x in css_blocks]]:
                css_blocks.append(f"<!-- wp:html -->{clean}<!-- /wp:html -->")
        if ('ps-dark-toggle' in clean or 'ps-theme-toggle' in clean) and not toggle_block:
            toggle_block = f"<!-- wp:html -->{clean}<!-- /wp:html -->"
    if len(css_blocks) >= 2 and toggle_block:
        print(f"Got CSS+toggle from: {p['slug']}")
        break

print(f"CSS blocks: {len(css_blocks)}, Toggle: {'yes' if toggle_block else 'no'}")

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
<a href="/sign-up/" style="display:block;background:#2B6CB0;color:#fff;text-align:center;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:0.95rem;transition:background 0.2s;">Get Started</a>
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
<a href="/sign-up/" style="display:block;background:#2B6CB0;color:#fff;text-align:center;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:0.95rem;transition:background 0.2s;">Get Started</a>
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
<a href="/sign-up/" style="display:block;background:#2B6CB0;color:#fff;text-align:center;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:0.95rem;transition:background 0.2s;">Get Started</a>
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

# Build full content
parts = css_blocks + ([toggle_block] if toggle_block else []) + [PRICING_HTML]
new_content = "\n\n".join(parts)

pricing_id = None
for p in pages:
    if p['slug'] == 'pricing':
        pricing_id = p['id']
        break

r = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pricing_id}", json={"content": new_content})
print(f"Update pricing: {r.status_code}")
if r.status_code == 200:
    print("Done - pricing page rebuilt with CSS + toggle + content")
