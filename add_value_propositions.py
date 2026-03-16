"""Replace the pricing cards section with a two-column layout: value prop + pricing card per tier."""
import requests

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = s.get(f"{AZURE}/wp-json/wp/v2/pages?slug=pricing&context=edit")
page = r.json()[0]
pid = page['id']
content = page['content']['raw']
print(f"Page id={pid}, length={len(content)}")

marker = 'Pricing Plans'
idx = content.find(marker)
block_start = content.rfind('<!-- wp:html -->', 0, idx)
block_end = content.find('<!-- /wp:html -->', idx) + len('<!-- /wp:html -->')

print(f"Replacing pricing block: chars {block_start}..{block_end}")

VP_STYLE = "color:var(--ps-primary,#001F3F);font-size:1.15rem;font-weight:700;line-height:1.5;margin:0 0 12px;"
VP_BODY = "color:var(--ps-text,#374151);font-size:0.95rem;line-height:1.65;margin:0;"

NEW_PRICING = f'''<!-- wp:html -->
<div style="max-width:1100px;margin:0 auto;padding:0 20px;">

<div style="text-align:center;margin-bottom:32px;">
<h1 style="color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;margin-bottom:12px;">Pricing Plans</h1>
<p style="color:var(--ps-text,#374151);font-size:1.1rem;max-width:650px;margin:0 auto 12px;line-height:1.6;">Simple, transparent pricing based on the number of applications you choose. Cancel at any time.</p>
<p style="color:var(--ps-muted,#6B7280);font-size:0.9rem;font-style:italic;">Note: WordPress and PolySysMon each count as two applications.</p>
</div>

<!-- STARTER: value prop left, card right -->
<div class="ps-tier-row" style="display:grid;grid-template-columns:1fr 1fr;gap:28px;align-items:center;margin-bottom:36px;">
<div style="padding:20px 24px;">
<h3 style="{VP_STYLE}">At $29/user/mo, cheaper than most SaaS applications all by themselves.</h3>
<p style="{VP_BODY}">Pick one powerful app &mdash; Odoo for ERP, Nextcloud for file storage, Mattermost for team chat, or any of our 10 bundled applications &mdash; and get enterprise-grade, multi-tenant infrastructure on GCP. No vendor lock-in, no hidden fees.</p>
</div>
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
</div>

<!-- GROWTH: card left, value prop right (alternating) -->
<div class="ps-tier-row" style="display:grid;grid-template-columns:1fr 1fr;gap:28px;align-items:center;margin-bottom:36px;">
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
<div style="padding:20px 24px;">
<h3 style="{VP_STYLE}">At $49/user/mo, far cheaper than any 3 SaaS applications that stand alone and do not integrate.</h3>
<p style="{VP_BODY}">Choose any 3 applications and unlock dynamic orchestration &mdash; your apps talk to each other automatically. Odoo + Nextcloud + Mattermost working as one unified platform, with AI As Peers bringing intelligent agents into your team channels.</p>
</div>
</div>

<!-- UNLIMITED: value prop left, card right -->
<div class="ps-tier-row" style="display:grid;grid-template-columns:1fr 1fr;gap:28px;align-items:center;margin-bottom:36px;">
<div style="padding:20px 24px;">
<h3 style="{VP_STYLE}">At $99/user/mo, there is no limit to the SaaS applications you wish to integrate &mdash; Bundled or External.</h3>
<p style="{VP_BODY}">Every bundled application, every external integration, full PolySniffer network discovery, PolySysMon system monitoring, and custom atomic services built to your specifications. Dedicated support with SLA guarantees.</p>
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
@media (max-width:768px) {{
  .ps-tier-row {{ grid-template-columns: 1fr !important; gap: 20px !important; }}
}}
</style>
<!-- /wp:html -->'''

new_content = content[:block_start] + NEW_PRICING + content[block_end:]

r2 = s.post(f"{AZURE}/wp-json/wp/v2/pages/{pid}", json={"content": new_content})
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("Done - two-column value proposition pricing layout applied.")
else:
    print(f"Error: {r2.text[:400]}")
