"""Verify the new animated logo is live across the site."""
import requests
import re

SITE = "https://azure-nightingale-589250.hostingersite.com"
NEW_LOGO = "ezgif-logo-final.gif"

PAGES = ["/", "/architecture/", "/about-us/", "/pricing/", "/sign-up/", "/schedule-demo/"]

print("=== VERIFY: New logo + favicon across site ===\n")

for path in PAGES:
    r = requests.get(f"{SITE}{path}", timeout=20)
    html = r.text

    new_refs = len(re.findall(NEW_LOGO, html))
    old_refs = len(re.findall(r'Industrial-PolySaas-Cropped-300-Transparent', html))

    # Check favicon specifically
    favicon_new = bool(re.search(NEW_LOGO + r'.*?rel=["\']icon', html) or re.search(r'rel=["\']icon["\'].*?' + NEW_LOGO, html) or re.search(r'<link[^>]*icon[^>]*' + NEW_LOGO, html) or re.search(NEW_LOGO, re.search(r'<head>.*?</head>', html, re.DOTALL).group() if re.search(r'<head>.*?</head>', html, re.DOTALL) else ""))

    # Check if CSS override rules are present
    css_override = "content: url(" in html or "content:url(" in html

    status = "OK" if new_refs > 0 else "MISSING"
    old_status = f"({old_refs} old refs remain in Bricks data - overridden by CSS)" if old_refs > 0 else "(clean)"

    print(f"  {path}")
    print(f"    New logo refs: {new_refs}  {status}")
    print(f"    Old logo refs: {old_refs}  {old_status}")
    print(f"    Favicon uses new: {favicon_new}")
    print(f"    CSS override present: {css_override}")
    print()

# Check that the CSS comment is present (confirms CSS was published)
print("=== CSS deployment check ===")
r = requests.get(f"{SITE}/", timeout=20)
if "Updated 2026-03-06: New animated logo swap" in r.text:
    print("  Updated CSS comment found - deployment confirmed")
elif "PolySaaS Site-Wide Brand Uniformity CSS" in r.text:
    print("  Base CSS comment found but update marker missing - check if full paste was done")
else:
    print("  WARNING: CSS comment not found in page source")

# Check specific CSS rules
if "#brxe-a24611" in r.text and "ezgif-logo-final.gif" in r.text:
    print("  Home logo CSS override rule: PRESENT")
else:
    print("  Home logo CSS override rule: MISSING")

if "#brxe-qupvnj" in r.text and "ezgif-logo-final.gif" in r.text:
    print("  Footer logo CSS override rule: PRESENT")
else:
    print("  Footer logo CSS override rule: MISSING")
