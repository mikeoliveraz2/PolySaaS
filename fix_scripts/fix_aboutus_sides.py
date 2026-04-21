"""Remove white side gaps on About Us page."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Check rendered HTML to understand the white gap source
r = requests.get(BASE + "/about-us/", timeout=30)
html = r.text

# Check body classes
body_m = re.search(r'<body[^>]*class="([^"]*)"', html)
if body_m:
    print(f"Body classes: {body_m.group(1)[:300]}")

# Check entry-content-wrap context
ecw = html.find('entry-content-wrap')
if ecw > 0:
    print(f"\nentry-content-wrap found at {ecw}")

# The white sides come from the Kadence boxed content style.
# We need to add CSS to the About Us page (or use site-wide approach).
# Let's check if the About Us page already has a style block we can add to.
r2 = requests.get(BASE + "/wp-json/wp/v2/pages/1345",
                  params={"context": "edit", "_fields": "content"},
                  auth=AUTH, timeout=45)
content = r2.json()["content"]["raw"]
print(f"\nAbout Us content length: {len(content)} chars")

# Check if there's already a <style> block
style_pos = content.find('<style')
print(f"Existing <style> at: {style_pos}")

# Show first 500 chars
print(f"\nFirst 500 chars:\n{content[:500]}")
