"""Inspect HubSpot /home/ HTML asset URLs and rewrite output."""
import os, sys, re
sys.path.insert(0, r'F:\PolySaaS')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django; django.setup()

import requests
from django.db import connection
from dose.models import TenantApp, Tenant
from dose.polysniffer.handlers.hubspot_native_sniff import _rewrite_hubspot_native_html
from dose.passthrough.handlers.hubspot_handler import HubspotPassthroughHandler

with connection.cursor() as cur:
    cur.execute("SET search_path TO public")
tenant = Tenant.objects.filter(slug='olient').first()
ta = TenantApp.public_bundles.filter(tenant=tenant, app_name='hubspot').first()
extra = ta.extra_config or {}
cookies = extra.get('hs_web_cookies') or {}
hub = extra.get('hs_hub_subdomain', 'app-na2.hubspot.com')
print(f"hub={hub} cookies={list(cookies.keys())}")

cookie_header = '; '.join(f'{k}={v}' for k, v in cookies.items())
for path in ('/home/', '/home/?portalId=246571499'):
    url = f'https://{hub}{path}'
    resp = requests.get(url, headers={
        'Cookie': cookie_header,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0',
        'Accept': 'text/html',
    }, allow_redirects=True, timeout=20)
    print(f"\n=== GET {url} -> {resp.status_code} final={resp.url} ct={resp.headers.get('content-type','')[:40]}")
    html = resp.text
    print(f"len={len(html)} has shim marker would need injection")
    for pat in (r'<link[^>]+href=["\']([^"\']+)["\']', r'<script[^>]+src=["\']([^"\']+)["\']'):
        hits = re.findall(pat, html[:50000], re.I)
        print(f"  first assets ({pat[:20]}...):")
        for h in hits[:8]:
            print(f"    {h[:120]}")
    handler = HubspotPassthroughHandler()
    proxy = '/pt/admin/app.hubspot.com'
    rewritten = _rewrite_hubspot_native_html(
        html[:80000],
        base_origin='https://app.hubspot.com',
        proxy_prefix=proxy,
        handler=handler,
        known_bases={'https://app.hubspot.com', f'https://{hub}'},
    )
    for pat in (r'<link[^>]+href=["\']([^"\']+)["\']', r'<script[^>]+src=["\']([^"\']+)["\']'):
        hits = re.findall(pat, rewritten[:50000], re.I)
        print(f"  REWRITTEN assets:")
        for h in hits[:8]:
            print(f"    {h[:120]}")
