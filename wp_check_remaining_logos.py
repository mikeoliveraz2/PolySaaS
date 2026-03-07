"""Check which pages still show the old logo after site identity update."""
import requests
import re

SITE = "https://azure-nightingale-589250.hostingersite.com"

PAGES = [
    "/",
    "/architecture/",
    "/sign-up/",
    "/about-us/",
    "/bundled-applications/",
    "/pricing/",
    "/atomic-services/",
    "/polysniffer/",
    "/ai-as-peers/",
    "/schedule-demo/",
    "/odoo/",
    "/liferay-2/",
    "/nextcloud/",
    "/portal/",
    "/wordpress/",
    "/polysysmon/",
]

OLD_PATTERNS = [
    "Industrial-PolySaas-Cropped-300-Transparent",
    "Industrial-PolySaas-Logo-Transparent",
    "PolySaaS-Industrial-Logo-BIG",
]

print("=== POST-UPDATE: Checking all pages for remaining old logo references ===\n")

for path in PAGES:
    try:
        r = requests.get(f"{SITE}{path}", timeout=20)
        if r.status_code != 200:
            print(f"  {path}: HTTP {r.status_code}")
            continue

        html = r.text
        locations = []

        for pat in OLD_PATTERNS:
            # Find all occurrences with context
            for m in re.finditer(re.escape(pat), html):
                start = max(0, m.start() - 100)
                end = min(len(html), m.end() + 100)
                context = html[start:end].replace('\n', ' ')
                # Determine if it's in a favicon link, img, or other element
                if '<link' in context and ('icon' in context or 'apple-touch' in context):
                    loc_type = "FAVICON"
                elif '<img' in context:
                    loc_type = "IMG"
                elif 'background' in context:
                    loc_type = "BG-IMAGE"
                elif '<meta' in context:
                    loc_type = "META"
                else:
                    loc_type = "OTHER"
                locations.append((loc_type, pat))

        if locations:
            print(f"  {path}: STILL HAS OLD LOGO")
            seen = set()
            for loc_type, pat in locations:
                key = f"{loc_type}:{pat}"
                if key not in seen:
                    seen.add(key)
                    print(f"    [{loc_type}] {pat}")
        else:
            print(f"  {path}: CLEAN - no old logo references")

    except Exception as e:
        print(f"  {path}: error - {e}")

# Also check if new logo appears in favicon
print("\n=== NEW LOGO IN FAVICON ===")
r = requests.get(f"{SITE}/", timeout=20)
new_favicon = re.findall(r'<link[^>]*rel=["\'](?:icon|shortcut icon|apple-touch-icon)["\'][^>]*href=["\']([^"\']+)["\']', r.text, re.IGNORECASE)
new_favicon += re.findall(r'<link[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\'](?:icon|shortcut icon|apple-touch-icon)["\']', r.text, re.IGNORECASE)
for fav in new_favicon:
    print(f"  {fav}")

# Check for new logo appearing anywhere
print("\n=== NEW LOGO APPEARANCES ===")
new_refs = re.findall(r'ezgif-logo-final', r.text)
print(f"  Home page: {len(new_refs)} references to ezgif-logo-final")
