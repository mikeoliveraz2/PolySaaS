"""Fetch Dolibarr theme CSS through passthrough; check MIME and body."""
import os
import re
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

PREFIX = "/pt/admin/localhost:8083"
User = get_user_model()
u = User.objects.get(username="pso17")
c = Client()
c.force_login(u)
s = c.session
s["tenant_slug"] = "pso17"
s.save()

# Land on company/setup page like the screenshot
r = c.get(PREFIX + "/admin/company.php?mainmenu=home&leftmenu=setup", follow=True)
html = r.content.decode("utf-8", "replace")
print("land", r.status_code, "len", len(html))

hrefs = []
for L in re.findall(r"<link[^>]+>", html, re.I):
    if "stylesheet" not in L.lower() and "style.css" not in L.lower() and ".css" not in L.lower():
        continue
    hm = re.search(r"""href\s*=\s*["']([^"']+)["']""", L, re.I)
    if not hm:
        continue
    h = hm.group(1).replace("&amp;", "&")
    if "/pt/admin/" in h or h.startswith("/theme") or h.startswith("/includes"):
        hrefs.append(h)

print("doli css hrefs", len(hrefs))
for h in hrefs:
    print(" ", h[:180])

for h in hrefs:
    r2 = c.get(h)
    ct = (r2.get("Content-Type") or "").lower()
    body = r2.content
    ok_css = "text/css" in ct or "stylesheet" in ct
    htmlish = body[:200].lower().find(b"<html") >= 0 or body[:200].lower().find(b"<!doctype") >= 0
    print(
        f"FETCH {h.split('?')[0][-40:]} status={r2.status_code} ct={ct!r} "
        f"len={len(body)} ok_css={ok_css} htmlish={htmlish}"
    )
    if not ok_css or htmlish:
        print("  BAD START:", body[:160])
