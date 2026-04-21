"""Make the logo neural network background full width."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

IMG_URL = "https://polysaas.online/wp-content/uploads/2026/03/hero-bg-neural.jpg"

# Find the current logo wrapper with the 400px rounded card
pat = r"<div style=\"background:url\('" + re.escape(IMG_URL) + r"'\)[^\"]*\">\s*<div style=\"position:absolute[^\"]*\"></div>\s*<div style=\"position:relative[^\"]*\">\s*<figure[^>]*><img[^>]*Industrial-PolySaas-Cropped-300-Transparent\.png[^>]*/>\s*</figure>\s*</div>\s*</div>"

m = re.search(pat, content)
if m:
    old_block = m.group(0)
    print(f"Found current logo wrapper ({len(old_block)} chars)")
else:
    print("Not found via regex, searching manually...")
    pos = content.find("hero-bg-neural")
    if pos > 0:
        start = max(0, pos - 200)
        end = min(len(content), pos + 600)
        print(content[start:end])
    sys.exit(1)

# Replace with full-width version
new_block = f'''<div style="background:url('{IMG_URL}') center/cover no-repeat;padding:35px 20px;margin:0 -2rem;text-align:center;position:relative">
  <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(15,23,42,0.45)"></div>
  <div style="position:relative;z-index:1;text-align:center">
    <figure style="margin:0;display:inline-block"><img decoding="async" src="https://polysaas.online/wp-content/uploads/2025/12/Industrial-PolySaas-Cropped-300-Transparent.png" alt="PolySaaS Logo" style="width:300px;filter:drop-shadow(0 2px 8px rgba(0,0,0,0.3))" /></figure>
  </div>
</div>'''

content = content.replace(old_block, new_block)
print("Replaced with full-width background")

r2 = requests.post(BASE + "/wp-json/wp/v2/pages/1313",
                   auth=AUTH,
                   json={"content": content},
                   timeout=45)
print(f"Update: {r2.status_code}")
if r2.status_code == 200:
    print("SUCCESS - Logo background is now full width")
else:
    print(f"Error: {r2.text[:300]}")
