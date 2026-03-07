import requests
import re

WP_URL = "https://azure-nightingale-589250.hostingersite.com"

PAGES = [
    "/",
    "/architecture/",
    "/sign-up/",
    "/schedule-demo/",
    "/about-us/",
    "/bundled-applications/",
    "/pricing/",
    "/contact/",
    "/atomic-services/",
    "/polysniffer/",
    "/ai-as-peers/",
]

OLD_PATTERNS = [
    "Industrial-PolySaas-Cropped-300-Transparent",
    "Industrial-PolySaas-Logo-Transparent",
    "PolySaaS-Industrial-Logo-BIG",
]

print("=== DEEP SCAN: Old logo references across all pages ===\n")

for page in PAGES:
    try:
        r = requests.get(f"{WP_URL}{page}", timeout=20)
        if r.status_code != 200:
            print(f"  {page}: HTTP {r.status_code}")
            continue

        html = r.text
        found = []
        for pat in OLD_PATTERNS:
            matches = re.findall(r'[^"\'>\s]*' + re.escape(pat) + r'[^"\'<\s]*', html)
            for m in matches:
                if m not in found:
                    found.append(m)

        # Also find the header/logo area
        header_imgs = re.findall(r'<header[^>]*>.*?</header>', html, re.DOTALL | re.IGNORECASE)
        nav_imgs = re.findall(r'<nav[^>]*>.*?</nav>', html, re.DOTALL | re.IGNORECASE)

        # Find ALL img srcs in header/nav area
        header_nav_text = " ".join(header_imgs + nav_imgs)
        header_img_srcs = re.findall(r'src=["\']([^"\']+)["\']', header_nav_text)

        if found:
            print(f"  {page}: OLD LOGO FOUND")
            for f_item in found:
                print(f"    -> {f_item}")
        else:
            print(f"  {page}: no old logo refs")

        if header_img_srcs:
            print(f"    Header/Nav images:")
            for src in header_img_srcs:
                print(f"      {src}")

    except Exception as e:
        print(f"  {page}: error - {e}")

# Also check the favicon / site icon
print("\n=== CHECKING FAVICON / SITE ICON ===")
r = requests.get(f"{WP_URL}/", timeout=20)
favicons = re.findall(r'<link[^>]*rel=["\'](?:icon|shortcut icon|apple-touch-icon)["\'][^>]*href=["\']([^"\']+)["\']', r.text, re.IGNORECASE)
favicons += re.findall(r'<link[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\'](?:icon|shortcut icon|apple-touch-icon)["\']', r.text, re.IGNORECASE)
for fav in favicons:
    print(f"  Favicon: {fav}")

# Check the site_icon meta
site_icons = re.findall(r'<link[^>]*rel=["\'](?:icon|apple-touch-icon)["\'][^>]*>', r.text, re.IGNORECASE)
for si in site_icons:
    print(f"  Icon link tag: {si}")

# Check for Bricks-specific logo element
print("\n=== CHECKING FOR BRICKS LOGO ELEMENT ===")
bricks_logo = re.findall(r'class=["\'][^"\']*brxe-logo[^"\']*["\'].*?(?:</[^>]+>)', r.text, re.DOTALL)
if bricks_logo:
    for bl in bricks_logo:
        print(f"  Bricks logo element: {bl[:500]}")
else:
    # Look for any element with "logo" in class
    logo_els = re.findall(r'<[^>]*class=["\'][^"\']*logo[^"\']*["\'][^>]*>.*?</[^>]+>', r.text[:10000], re.DOTALL | re.IGNORECASE)
    for le in logo_els[:5]:
        print(f"  Logo-class element: {le[:400]}")

# Show the first 5000 chars around the header area
print("\n=== HEADER AREA HTML (first occurrence) ===")
header_match = re.search(r'<header[^>]*>.*?</header>', r.text, re.DOTALL | re.IGNORECASE)
if header_match:
    print(header_match.group()[:3000])
else:
    # Look for brx-header
    brx_header = re.search(r'<div[^>]*id=["\']brx-header["\'][^>]*>.*?(?=<section|<main|<div[^>]*id=["\']brx-content)', r.text, re.DOTALL)
    if brx_header:
        print(brx_header.group()[:3000])
    else:
        print("  No header/brx-header found")
