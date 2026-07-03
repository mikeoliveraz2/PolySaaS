import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory
from dose.passthrough.handlers.hubspot_handler import HubspotPassthroughHandler
from dose.models import PassThroughEndpoint

c = Client()
user = get_user_model().objects.get(username__iexact="olientadmin")
c.force_login(user)
s = c.session
s["tenant_slug"] = "olient"
s.save()

ep = PassThroughEndpoint.objects.filter(endpoint_url__icontains="hubspot").first()
print("endpoint", ep.id if ep else None, ep.endpoint_url if ep else None)

for path in (
    "/pt/admin/app.hubspot.com/",
    "/pt/admin/app.hubspot.com/home/",
    "/pt/admin/app.hubspot.com/undefined/",
):
    r = c.get(path, follow=False)
    loc = r.get("Location", "")
    print(f"\n=== GET {path} -> {r.status_code} loc={loc[:80] if loc else ''}")
    if r.status_code in (301, 302, 303, 307, 308) and loc:
        continue
    html = r.content.decode("utf-8", errors="replace")
    title = ""
    import re

    m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
    if m:
        title = m.group(1).strip()
    css = re.findall(r'href="(https://static\.hsappstatic\.net[^"]+\.css)"', html)
    print("title:", title)
    print("css count:", len(css))
    for u in css[:5]:
        print(" ", u[:100])
    if "PORTAL_BOOTSTRAP_JSON" in html:
        idx = html.find("PORTAL_BOOTSTRAP_JSON = ")
        chunk = html[idx : idx + 200]
        print("portal bootstrap snippet:", chunk[:180])

rf = RequestFactory()
req = rf.get("/pt/admin/app.hubspot.com/home/")
req.user = user
req.session = s
handler = HubspotPassthroughHandler(endpoint=ep)
handler._bind_hubspot_request(req)
body, status, ct = handler._build_portal_bootstrap_payload(req)
print("\nportal bootstrap API body len:", len(body), "status", status)
try:
    j = json.loads(body.decode())
    print("portalId:", j.get("portalId"), "keys:", list(j.keys())[:8])
except Exception as e:
    print("json err", e, body[:200])
