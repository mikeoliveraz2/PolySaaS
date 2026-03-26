"""Upload neural network background and apply to hero section."""
import requests, re, sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Upload the hero background image (compressed JPEG)
img_path = r"C:\Users\PC\.cursor\projects\d-PolySaaS\assets\hero-bg-neural.jpg"

with open(img_path, "rb") as f:
    img_data = f.read()
print(f"Image size: {len(img_data)} bytes")

r1 = requests.post(
    BASE + "/wp-json/wp/v2/media",
    auth=AUTH,
    headers={
        "Content-Disposition": "attachment; filename=hero-bg-neural.jpg",
        "Content-Type": "image/jpeg",
    },
    data=img_data,
    timeout=60
)
print(f"Upload: {r1.status_code}")
if r1.status_code == 201:
    media = r1.json()
    img_url = media["source_url"]
    print(f"Uploaded: {img_url}")
else:
    print(f"Error: {r1.text[:300]}")
    sys.exit(1)

# Now update the hero section on the homepage
r2 = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                  params={"context": "edit", "_fields": "content"},
                  auth=AUTH, timeout=45)
content = r2.json()["content"]["raw"]

# The current hero heading
old_hero = '<!-- wp:html -->\n<h2 style="text-align:center;padding:5px 0 0 0;margin:0;color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;">Industrial Strength SaaS for Limitless Horizons</h2>\n<!-- /wp:html -->'

if old_hero not in content:
    # Try without newlines
    old_hero = '<!-- wp:html -->\r\n<h2 style="text-align:center;padding:5px 0 0 0;margin:0;color:var(--ps-primary,#001F3F);font-size:2rem;font-weight:700;">Industrial Strength SaaS for Limitless Horizons</h2>\r\n<!-- /wp:html -->'

if old_hero not in content:
    # Try to find it with regex
    pattern = r'<!-- wp:html -->\s*<h2 style="text-align:center;padding:5px 0 0 0;margin:0;color:var\(--ps-primary,#001F3F\);font-size:2rem;font-weight:700;">Industrial Strength SaaS for Limitless Horizons</h2>\s*<!-- /wp:html -->'
    match = re.search(pattern, content)
    if match:
        old_hero = match.group(0)
        print(f"Found hero via regex ({len(old_hero)} chars)")
    else:
        print("Hero heading not found! Searching...")
        pos = content.find('Industrial Strength SaaS')
        if pos > 0:
            start = max(0, pos - 200)
            end = min(len(content), pos + 200)
            print(f"Context:\n{content[start:end]}")
        sys.exit(1)

# Find the PolySaaS logo image that comes after the hero heading
# It's the big centered logo
logo_pattern = r'(<!-- wp:image.*?PolySaaS.*?<!-- /wp:image -->)'
logo_match = re.search(logo_pattern, content[content.find(old_hero):content.find(old_hero)+2000], re.DOTALL)
logo_block = ""
if logo_match:
    logo_block = logo_match.group(1)
    print(f"Found logo block ({len(logo_block)} chars)")

# New hero section with background image
new_hero = f'''<!-- wp:html -->
<div style="background:url('{img_url}') center/cover no-repeat;padding:40px 20px 30px;margin:-2rem -2rem 0 -2rem;text-align:center;position:relative">
  <div style="position:absolute;top:0;left:0;right:0;bottom:0;background:rgba(15,23,42,0.55)"></div>
  <div style="position:relative;z-index:1;max-width:900px;margin:0 auto">
    <h2 style="text-align:center;padding:0;margin:0 0 10px;color:#FFFFFF;font-size:2.2rem;font-weight:700;text-shadow:0 2px 8px rgba(0,0,0,0.4)">Industrial Strength SaaS for Limitless Horizons</h2>
  </div>
</div>
<!-- /wp:html -->'''

# Replace old hero with new
new_content = content.replace(old_hero, new_hero)

# Verify the change was made
if new_content == content:
    print("ERROR: No change made!")
    sys.exit(1)

r3 = requests.post(BASE + "/wp-json/wp/v2/pages/1313",
                   auth=AUTH,
                   json={"content": new_content},
                   timeout=45)
print(f"Update: {r3.status_code}")
if r3.status_code == 200:
    print("SUCCESS - Hero section now has AI neural network background")
else:
    print(f"Error: {r3.text[:300]}")
