"""Verify that the site-wide CSS was applied by checking for the custom_css post
and checking if off-brand colors are now overridden on rendered pages."""
import requests
import re

SITE = "https://azure-nightingale-589250.hostingersite.com"
USER = "mikeoliveraz@gmail.com"
APP_PASS = "vlop MpGU Os2V xDSI C6T7 2fAN"

session = requests.Session()
session.auth = (USER, APP_PASS)

# Check custom_css posts
print("Checking custom_css posts on WordPress...")
resp = session.get(f"{SITE}/wp-json/wp/v2/posts", params={"type": "custom_css", "status": "any", "per_page": 10})
print(f"  Posts endpoint: HTTP {resp.status_code}")

# Check the rendered HTML of the home page for our CSS marker comment
print("\nChecking rendered Home page for applied CSS...")
resp = requests.get(f"{SITE}/", headers={'User-Agent': 'PolySaaS-Verify/1.0'}, timeout=15)
html = resp.text

if 'PolySaaS Site-Wide Brand Uniformity CSS' in html:
    print("  SUCCESS: Site-wide CSS found in rendered HTML!")
elif 'PolySaaS Home Page Fixes' in html:
    print("  PARTIAL: Only the old home-page CSS is present.")
else:
    print("  NOT FOUND: CSS not detected in rendered HTML.")

# Check if our specific overrides appear in the page
style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
all_styles = '\n'.join(style_blocks)

checks = [
    ('#brxe-9d3229', 'background-image: none', 'Green stripe fix'),
    ('#brxe-spdnfe', 'background-color: #003399', 'Sign Up button fix'),
    ('#brxe-lxtgtl', 'background-color: #003399', 'Architecture CTA fix'),
    ('#brxe-wjsthw', 'background-color: #003399', 'Odoo button fix'),
]

print("\nChecking for specific override rules in Home page HTML:")
for selector, prop, desc in checks:
    if selector in all_styles and prop in all_styles:
        print(f"  [FOUND]  {desc} ({selector})")
    else:
        print(f"  [MISSING] {desc} ({selector})")

# Also check a different page (Architecture) for the CTA button fix
print("\nChecking Architecture page...")
resp2 = requests.get(f"{SITE}/architecture/", headers={'User-Agent': 'PolySaaS-Verify/1.0'}, timeout=15)
html2 = resp2.text
if 'PolySaaS Site-Wide Brand Uniformity CSS' in html2:
    print("  SUCCESS: Site-wide CSS found on Architecture page!")
elif '#brxe-lxtgtl' in html2 and '#003399' in html2:
    print("  CSS rules present (may be in custom_css output).")
else:
    print("  CSS not detected on Architecture page.")

# Check Odoo page
print("\nChecking Odoo page...")
resp3 = requests.get(f"{SITE}/odoo/", headers={'User-Agent': 'PolySaaS-Verify/1.0'}, timeout=15)
html3 = resp3.text
if 'PolySaaS Site-Wide Brand Uniformity CSS' in html3:
    print("  SUCCESS: Site-wide CSS found on Odoo page!")
elif '#brxe-wjsthw' in html3 and '#003399' in html3:
    print("  CSS override present for Odoo button.")
else:
    print("  CSS not detected on Odoo page.")

print("\nVerification complete.")
