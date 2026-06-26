import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

import dose.polysniffer.sniff_forward as sf

# patch should be applied via hubspot_native_sniff import
print("patched", getattr(sf, "_hubspot_cdn_upstream_patched", False))

cases = [
    "//static.hsappstatic.net/LoginUI/static-1.15478/bundles/project.js",
    "/static.hsappstatic.net/react-dlb/static-1.81/bundle.production.js",
    "/login",
]
for sub in cases:
    url, path = sf._resolve_upstream_url("https://app-na2.hubspot.com/", sub)
    print(sub[:50], "->", url[:90])
