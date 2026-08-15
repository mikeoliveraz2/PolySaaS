"""Probe Dolibarr CSS via passthrough host-based prefix."""
import os
import re
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from urllib.parse import urlparse

PREFIX = "/pt/admin/localhost:8083"
User = get_user_model()
u = User.objects.get(username="pso17")
c = Client()
c.force_login(u)
s = c.session
s["tenant_slug"] = "pso17"
s.save()

r = c.get(PREFIX + "/", follow=False)
print("PAGE", r.status_code, r.get("Content-Type"), "len", len(r.content))
# follow redirects manually a few hops
hops = 0
while r.status_code in (301, 302, 303, 307, 308) and hops < 8:
    loc = r.get("Location") or ""
    print(" REDIRECT", loc)
    r = c.get(loc, follow=False)
    hops += 1
    print("PAGE", r.status_code, r.get("Content-Type"), "len", len(r.content))

html = r.content.decode("utf-8", "replace")
m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
if m:
    print("TITLE:", re.sub(r"\s+", " ", m.group(1)).strip()[:140])

links = re.findall(r"<link[^>]+>", html, re.I)
css_links = [L for L in links if "stylesheet" in L.lower() or ".css" in L.lower() or "style.css" in L.lower()]
print("css link tags", len(css_links))
hrefs = []
for L in css_links[:20]:
    hm = re.search(r"""href\s*=\s*["']([^"']+)["']""", L, re.I)
    if hm:
        hrefs.append(hm.group(1))
        print(" HREF", hm.group(1)[:160])

unprefixed = [h for h in hrefs if h.startswith("/theme/") or h.startswith("/includes/")]
print("UNPREFIXED", unprefixed)

# Also search raw for style.css.php anywhere
raw_css = re.findall(r'["\']([^"\']*style\.css\.php[^"\']*)["\']', html)
print("style.css.php refs", raw_css[:5])

targets = hrefs[:6] or [
    PREFIX + "/theme/eldy/style.css.php?lang=en_US&theme=eldy&entity=1&layout=classic&version=23.0.2&revision=0",
    PREFIX + "/includes/jquery/css/base/jquery-ui.css?layout=classic&version=23.0.2",
]
for h in targets:
    if h.startswith("http"):
        p = urlparse(h)
        url = p.path + (("?" + p.query) if p.query else "")
    else:
        url = h
    print("---", url[:140])
    r2 = c.get(url)
    ct = r2.get("Content-Type")
    body = r2.content[:120]
    print(" status", r2.status_code, "CT", ct, "len", len(r2.content))
    print(" start", body)
    low = body.lower()
    if b"<html" in low or b"<!doctype" in low or b"<script" in low or b"login" in low:
        print(" WARNING: looks like HTML/login not CSS")
