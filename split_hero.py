"""Move heading back outside the background, keep bg on logo only."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

IMG_URL = "https://polysaas.online/wp-content/uploads/2026/03/hero-bg-serverroom.jpg"

# Find the current combined block (heading + logo inside bg)
pat = r'<!-- wp:html -->\s*<div style="background:url\(\'' + re.escape(IMG_URL) + r'\'\)[^"]*">\s*<div style="position:absolute[^"]*"></div>\s*<div style="position:relative[^"]*">.*?</div>\s*</div>\s*<!-- /wp:html -->'
m = re.search(pat, content, re.DOTALL)
if m:
    old_block = m.group(0)
    print(f"Found combined block ({len(old_block)} chars)")
else:
    print("Combined block not found!")
    pos = content.find("hero-bg-serverroom")
    if pos > 0:
        print(content[max(0,pos-200):pos+800])
    sys.exit(1)

# Replace with: plain heading THEN bg-wrapped logo
new_blocks = f'''<!-- wp:html -->
<h2 style="text-align:center;padding:5px 0 0 0;margin:0;color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;">Industrial Strength SaaS for Limitless Horizons</h2>
<!-- /wp:html -->
<!-- wp:html -->
<div style="background:url('{IMG_URL}') center/cover no-repeat;padding:35px 20px;margin:0 -2rem;text-align:center;position:relative">
  <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(15,23,42,0.45)"></div>
  <div style="position:relative;z-index:1;text-align:center">
    <figure style="margin:0;display:inline-block"><img decoding="async" src="https://polysaas.online/wp-content/uploads/2025/12/Industrial-PolySaas-Cropped-300-Transparent.png" alt="PolySaaS Logo" style="width:300px;filter:drop-shadow(0 2px 8px rgba(0,0,0,0.3))" /></figure>
  </div>
</div>
<!-- /wp:html -->'''

content = content.replace(old_block, new_blocks)

r2 = requests.post(BASE + "/wp-json/wp/v2/pages/1313",
                   auth=AUTH,
                   json={"content": content},
                   timeout=45)
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("SUCCESS - Heading outside, bg on logo only")
else:
    print(f"Error: {r2.text[:300]}")
