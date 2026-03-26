"""Add CTA button section to investor page, above the footer."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/2565",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# Insert CTA before the footer block
footer_marker = '<div style="max-width:1200px;margin:20px auto 0;background:var(--ps-footer-bg)'

cta_block = '''<!-- wp:html -->
<div style="max-width:800px;margin:40px auto 30px;text-align:center;padding:36px 24px;border-radius:10px;background:linear-gradient(135deg,var(--ps-card-bg,#F9FAFB),var(--ps-bg-alt,#F3F4F6));border:1px solid var(--ps-border,#E5E7EB)">
  <h3 style="margin:0 0 8px;font-size:1.3rem;font-weight:700;color:var(--ps-primary,#001F3F)">Interested in Our Seed Round?</h3>
  <p style="margin:0 0 20px;font-size:0.95rem;color:#111827;line-height:1.6">We're raising $750K–$1.5M to accelerate go-to-market and scale the platform.<br>Let's schedule a conversation.</p>
  <a href="/schedule-demo/" style="display:inline-block;background:#0F766E;color:#fff;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600;font-size:0.95rem;letter-spacing:0.3px;margin-right:12px">Schedule a Meeting</a>
  <a href="mailto:michael.oliver@polysaas.online" style="display:inline-block;background:transparent;color:#0F766E;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600;font-size:0.95rem;letter-spacing:0.3px;border:2px solid #0F766E">Email Us</a>
</div>
<!-- /wp:html -->

'''

if footer_marker in content:
    content = content.replace(footer_marker, cta_block + footer_marker)
    print("Inserted CTA before footer")
else:
    print("Footer marker not found!")
    sys.exit(1)

r2 = requests.post(BASE + "/wp-json/wp/v2/pages/2565",
                   auth=AUTH,
                   json={"content": content},
                   timeout=45)
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("SUCCESS - CTA buttons added to investor page")
else:
    print(f"Error: {r2.text[:300]}")
