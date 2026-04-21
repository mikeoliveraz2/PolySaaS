"""Move neural network bg to logo only, revert heading to plain."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

IMG_URL = "https://polysaas.online/wp-content/uploads/2026/03/hero-bg-neural.jpg"

# Step 1: Revert the hero heading - replace the bg-wrapped version with the original plain heading
old_hero = '''<!-- wp:html -->
<div style="background:url('https://polysaas.online/wp-content/uploads/2026/03/hero-bg-neural.jpg') center/cover no-repeat;padding:40px 20px 30px;margin:-2rem -2rem 0 -2rem;text-align:center;position:relative">
  <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(15,23,42,0.55)"></div>
  <div style="position:relative;z-index:1;max-width:900px;margin:0 auto">
    <h2 style="text-align:center;padding:0;margin:0 0 10px;color:#FFFFFF;font-size:2.2rem;font-weight:700;text-shadow:0 2px 8px rgba(0,0,0,0.4)">Industrial Strength SaaS for Limitless Horizons</h2>
  </div>
</div>
<!-- /wp:html -->'''

original_heading = '''<!-- wp:html -->
<h2 style="text-align:center;padding:5px 0 0 0;margin:0;color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;">Industrial Strength SaaS for Limitless Horizons</h2>
<!-- /wp:html -->'''

if old_hero in content:
    content = content.replace(old_hero, original_heading)
    print("Step 1: Reverted heading to plain")
else:
    print("Step 1: Hero bg wrapper not found, trying regex...")
    pat = r'<!-- wp:html -->\s*<div style="background:url\(.*?hero-bg-neural.*?</div>\s*</div>\s*</div>\s*<!-- /wp:html -->'
    m = re.search(pat, content, re.DOTALL)
    if m:
        content = content.replace(m.group(0), original_heading)
        print("Step 1: Reverted heading via regex")
    else:
        print("Step 1: WARNING - could not find hero bg wrapper")

# Step 2: Wrap the logo image block with neural network background
old_logo = '<div class="wp-block-image" style="text-align:center">\n<figure class="aligncenter size-full is-resized"><img decoding="async" src="https://polysaas.online/wp-content/uploads/2025/12/Industrial-PolySaas-Cropped-300-Transparent.png" alt="PolySaaS Logo" style="width:300px" /></figure>\n</div>'

if old_logo not in content:
    # Try to find with regex
    pat2 = r'<div class="wp-block-image"[^>]*>\s*<figure[^>]*><img[^>]*Industrial-PolySaas-Cropped-300-Transparent\.png[^>]*/>\s*</figure>\s*</div>'
    m2 = re.search(pat2, content)
    if m2:
        old_logo = m2.group(0)
        print(f"Found logo block via regex ({len(old_logo)} chars)")
    else:
        print("ERROR: Logo block not found!")
        sys.exit(1)

new_logo = f'''<div style="background:url('{IMG_URL}') center/cover no-repeat;border-radius:12px;padding:30px 20px;margin:0 auto;max-width:400px;position:relative;box-shadow:0 4px 24px rgba(0,0,0,0.2)">
  <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(15,23,42,0.45);border-radius:12px"></div>
  <div style="position:relative;z-index:1;text-align:center">
    <figure style="margin:0;display:inline-block"><img decoding="async" src="https://polysaas.online/wp-content/uploads/2025/12/Industrial-PolySaas-Cropped-300-Transparent.png" alt="PolySaaS Logo" style="width:300px;filter:drop-shadow(0 2px 8px rgba(0,0,0,0.3))" /></figure>
  </div>
</div>'''

content = content.replace(old_logo, new_logo)
print("Step 2: Wrapped logo with neural network background")

# Save
r3 = requests.post(BASE + "/wp-json/wp/v2/pages/1313",
                   auth=AUTH,
                   json={"content": content},
                   timeout=45)
print(f"Update: {r3.status_code}")
if r3.status_code == 200:
    print("SUCCESS - Neural network bg now on logo only")
else:
    print(f"Error: {r3.text[:300]}")
