"""Extract HubSpot embed body from passthrough response."""
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
c = Client()
c.force_login(User.objects.get(username__iexact="olientadmin"))
s = c.session
s["tenant_slug"] = "olient"
s.save()

r = c.get("/pt/admin/app.hubspot.com/home/")
html = r.content.decode("utf-8", errors="replace")

# scope div body
m = re.search(
    r'<div class="polysaas-passthrough-scope[^"]*"[^>]*>(.*)</div>\s*<p class="text-muted"',
    html,
    re.DOTALL | re.IGNORECASE,
)
body = m.group(1) if m else ""
print("scope_body_len", len(body))

for pat in ("svg", "viewBox", "home-redirect", "hs-loader", "Redirecting", "root.css", "hubspot-theme", "login-overlay", "ps-hs"):
    print(pat, body.lower().count(pat.lower()) if body else html.lower().count(pat.lower()))

# hubspot css in full page
for pat in (
    r'href="https://static[^"]+\.css"',
    r"hubspot-theme[^\"']*\.css",
    r"home-redirect-ui[^\"']*\.css",
):
    hits = re.findall(pat, html, re.I)
    print("CSS", pat, len(hits))
    for h in hits[:5]:
        print(" ", h[:120])

# overlay scripts
for pat in ("data-hs-login-overlay", "data-ps-hs-workspace-redirect", "connect HubSpot", "ps-hs-wait"):
    print(pat, html.count(pat))

out = os.path.join(os.path.dirname(__file__), "hs_body_sample.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(body[:50000] if body else html[-50000:])
print("wrote", out)
