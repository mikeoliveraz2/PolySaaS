"""Inspect HubSpot passthrough HTML for CSS issues."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()
u = User.objects.get(username__iexact="olientadmin")
c = Client()
c.force_login(u)

for path in (
    "/pt/admin/app.hubspot.com/",
    "/pt/admin/app.hubspot.com/home/",
):
    r = c.get(path)
    html = r.content.decode("utf-8", errors="replace")
    print("=" * 60)
    print("PATH", path, "status", r.status_code, "len", len(html))

    broken = re.findall(r'\.css""', html)
    print("broken_css_double", len(broken))

    links = re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', html, re.I)
    print("stylesheet_links", len(links))
    for L in links[:5]:
        print("  ", L[:220])

    proto = re.findall(r'href="//static[^"]+', html)
    print("proto_rel_cdn", len(proto))

    sniff_cdn = re.findall(r'/dose/sniff/[^"\']*static\.hsappstatic[^"\']*', html)
    print("sniff_proxy_cdn", len(sniff_cdn), sniff_cdn[:2])

    pt_cdn = re.findall(r'/pt/admin/[^"\']*static\.hsappstatic[^"\']*', html)
    print("pt_proxy_cdn", len(pt_cdn), pt_cdn[:2])

    canon = re.search(r"CANONICAL_HOST\s*=\s*['\"]([^'\"]+)", html)
    print("CANONICAL_HOST", canon.group(1) if canon else "NA")

    embed_body = "embed_body" in html or "home-redirect" in html.lower()
    print("has_home_redirect", "home-redirect" in html.lower())
    print("has_shim", "data-hubspot-pt-shim" in html)
    print("has_embed_src_link", bool(re.search(r'target="_blank"[^>]*>/pt/admin/app\.hubspot\.com/', html)))

    # Save snippet for manual review
    out = os.path.join(os.path.dirname(__file__), "hs_html_sample.html")
    if path.endswith("/home/"):
        with open(out, "w", encoding="utf-8") as f:
            f.write(html[:80000])
        print("wrote", out)
