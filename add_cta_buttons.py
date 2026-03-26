"""Add CTA buttons to the investor contact section."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/2565",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# Find the exact closing of the contact section
# The section ends with </div> before the disclaimer
old_close = '</div>\n<!-- /wp:html -->\n\n<!-- wp:html -->\n<div class="inv-disclaimer">'

if old_close not in content:
    # Try to find it with different whitespace
    import re
    pat = r'(</div>)\s*(<!-- /wp:html -->)\s*(<!-- wp:html -->)\s*(<div class="inv-disclaimer">)'
    m = re.search(pat, content)
    if m:
        old_close = m.group(0)
        print(f"Found close pattern via regex ({len(old_close)} chars)")
    else:
        # Just find the inv-cta closing div
        pos = content.find('inv-disclaimer')
        print(f"inv-disclaimer at {pos}")
        if pos > 0:
            snippet = content[pos-200:pos+50]
            print(f"Context: {snippet}")

if old_close in content:
    new_close = '''<div style="margin-top:24px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
  <a href="/schedule-demo/" style="display:inline-block;background:#0F766E;color:#fff;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600;font-size:0.95rem">Schedule a Meeting</a>
  <a href="mailto:michael.oliver@polysaas.online" style="display:inline-block;background:transparent;color:#0F766E;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600;font-size:0.95rem;border:2px solid #0F766E">Email Us</a>
</div>
''' + old_close
    content = content.replace(old_close, new_close)
    print("Added CTA buttons")
    
    r2 = requests.post(BASE + "/wp-json/wp/v2/pages/2565",
                       auth=AUTH,
                       json={"content": content},
                       timeout=45)
    print(f"Update: {r2.status_code}")
    if r2.status_code == 200:
        print("SUCCESS - CTA buttons added to contact section")
    else:
        print(f"Error: {r2.text[:300]}")
else:
    print("Could not find insertion point")
