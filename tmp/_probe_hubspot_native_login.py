"""Probe HubSpot native sniff HTML rewrite on login page."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

import requests
from dose.models import PassThroughEndpoint
from django.db import connection
from dose.polysniffer.sniff_handler_bridge import apply_native_sniff_rewrites
from dose.polysniffer.sniff_native_rewrite import sniff_native_proxy_prefix

ENDPOINT_URL = "https://app-na2.hubspot.com/"
LOGIN_PATH = "/login"
PROXY_PREFIX = "/dose/sniff/4/native"


class FakeRequest:
    path_info = "/dose/sniff/4/native/login"


def main():
    with connection.cursor() as c:
        c.execute('SET search_path TO "plysaast10", public')
    ep = PassThroughEndpoint.objects.filter(id=4).first()
    if not ep:
        with connection.cursor() as c:
            c.execute('SET search_path TO "public", public')
        ep = PassThroughEndpoint.objects.filter(id=4).first()
    print("endpoint:", ep.endpoint_url if ep else None)

    url = ENDPOINT_URL.rstrip("/") + LOGIN_PATH
    print("fetching", url)
    resp = requests.get(url, headers={"Accept-Encoding": "identity"}, timeout=30)
    print("status", resp.status_code, "len", len(resp.content))

    body = apply_native_sniff_rewrites(
        resp.content,
        content_type=resp.headers.get("Content-Type", ""),
        request=FakeRequest(),
        endpoint=ep,
        upstream_path=LOGIN_PATH,
        proxy_prefix=PROXY_PREFIX,
    )
    html = body.decode("utf-8", errors="replace")

    # sample src/href patterns
    srcs = re.findall(r'(?:src|href)=(["\'])([^"\']+)\1', html, flags=re.I)
    print("\nURL samples from rewritten HTML:")
    categories = {"cdn_https": 0, "sniff_proxy": 0, "broken_double": 0, "loginui_proxy": 0, "other": 0}
    for _, u in srcs[:80]:
        if u.startswith("https://static.hsappstatic.net"):
            categories["cdn_https"] += 1
            if categories["cdn_https"] <= 3:
                print("  CDN OK:", u[:100])
        elif "/dose/sniff/" in u and "hsappstatic" in u:
            categories["broken_double"] += 1
            print("  BROKEN CDN PROXY:", u[:120])
        elif u.startswith(PROXY_PREFIX) and "loginui" in u.lower():
            categories["loginui_proxy"] += 1
            if categories["loginui_proxy"] <= 5:
                print("  LOGINUI PROXIED:", u[:120])
        elif u.startswith(PROXY_PREFIX):
            categories["sniff_proxy"] += 1
        else:
            categories["other"] += 1

    print("\ncategories (first 80 attrs):", categories)

    # count all loginui proxy in full html
    bad = re.findall(r'/dose/sniff/\d+/native/[^"\']*[Ll]oginUI[^"\']*', html)
    print(f"\nTotal proxied LoginUI refs in HTML: {len(bad)}")
    if bad:
        print("  example:", bad[0][:140])


if __name__ == "__main__":
    main()
