"""Expand server room background to include the heading too."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# Find the heading block
heading = '<!-- wp:html -->\n<h2 style="text-align:center;padding:5px 0 0 0;margin:0;color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;">Industrial Strength SaaS for Limitless Horizons</h2>\n<!-- /wp:html -->'

if heading not in content:
    pat = r'<!-- wp:html -->\s*<h2[^>]*>Industrial Strength SaaS for Limitless Horizons</h2>\s*<!-- /wp:html -->'
    m = re.search(pat, content)
    if m:
        heading = m.group(0)
        print(f"Found heading via regex ({len(heading)} chars)")
    else:
        print("Heading not found!")
        sys.exit(1)
else:
    print("Found heading exactly")

# Find the bg wrapper with the logo
bg_pat = r"<div style=\"background:url\('https://polysaas\.online/wp-content/uploads/2026/03/hero-bg-serverroom\.jpg'\)[^\"]*\">\s*<div style=\"position:absolute[^\"]*\"></div>\s*<div style=\"position:relative[^\"]*\">\s*<figure[^>]*><img[^>]*Industrial-PolySaas-Cropped-300-Transparent\.png[^>]*/>\s*</figure>\s*</div>\s*</div>"
m2 = re.search(bg_pat, content)
if m2:
    old_bg = m2.group(0)
    print(f"Found bg wrapper ({len(old_bg)} chars)")
else:
    print("BG wrapper not found!")
    pos = content.find("hero-bg-serverroom")
    if pos > 0:
        print(content[max(0,pos-100):pos+600])
    sys.exit(1)

IMG_URL = "https://polysaas.online/wp-content/uploads/2026/03/hero-bg-serverroom.jpg"

# New combined block: heading + logo, both inside the background
new_combined = f'''<!-- wp:html -->
<div style="background:url('{IMG_URL}') center/cover no-repeat;padding:30px 20px 35px;margin:0 -2rem;text-align:center;position:relative">
  <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(15,23,42,0.45)"></div>
  <div style="position:relative;z-index:1;text-align:center;max-width:900px;margin:0 auto">
    <h2 style="text-align:center;padding:0;margin:0 0 16px;color:#FFFFFF;font-size:2.2rem;font-weight:700;text-shadow:0 2px 8px rgba(0,0,0,0.5)">Industrial Strength SaaS for Limitless Horizons</h2>
    <figure style="margin:0;display:inline-block"><img decoding="async" src="https://polysaas.online/wp-content/uploads/2025/12/Industrial-PolySaas-Cropped-300-Transparent.png" alt="PolySaaS Logo" style="width:300px;filter:drop-shadow(0 2px 8px rgba(0,0,0,0.3))" /></figure>
  </div>
</div>
<!-- /wp:html -->'''

# Remove the old heading block and replace the bg wrapper with the combined version
content = content.replace(heading, '')
content = content.replace(old_bg, new_combined)

r2 = requests.post(BASE + "/wp-json/wp/v2/pages/1313",
                   auth=AUTH,
                   json={"content": content},
                   timeout=45)
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("SUCCESS - Heading now inside server room background")
else:
    print(f"Error: {r2.text[:300]}")
