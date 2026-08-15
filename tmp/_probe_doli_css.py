"""Probe Dolibarr passthrough CSS: link hrefs + Content-Type of first stylesheet."""
import os
import re
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from urllib.parse import urlparse

User = get_user_model()
u = User.objects.get(username="pso17")
c = Client()
c.force_login(u)
s = c.session
s["tenant_slug"] = "pso17"
s.save()

r = c.get("/pt/admin/dolibarr/", follow=True)
print("page", r.status_code, r.get("Content-Type"), "bytes", len(r.content))
html = r.content.decode("utf-8", "replace")

# Are we still on login?
if "login" in html.lower()[:2000] and "DOLSESSID" not in str(r.cookies):
    print("NOTE: may be login page; sniff title")
print("title snippet:", re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S))
m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
if m:
    print("TITLE:", re.sub(r"\s+", " ", m.group(1)).strip()[:120])

links = re.findall(r"<link[^>]+>", html, re.I)
css_links = [L for L in links if "stylesheet" in L.lower() or ".css" in L.lower() or "style.css" in L.lower()]
print("link tags", len(links), "css-ish", len(css_links))
for L in css_links[:15]:
    print("LINK:", L[:350])

hrefs = []
for L in css_links:
    hm = re.search(r"""href\s*=\s*["']([^"']+)["']""", L, re.I)
    if hm:
        hrefs.append(hm.group(1))

print("HREFS:")
for h in hrefs[:20]:
    print(" ", h)

# Also check if stylesheets lack proxy prefix (escaped to upstream or site root)
bad = [h for h in hrefs if h.startswith("/theme/") or h.startswith("/includes/") or "localhost:8083" in h]
print("UNPREFIXED_OR_UPSTREAM", bad[:10])

for h in hrefs[:5]:
    if h.startswith("http"):
        p = urlparse(h)
        url = p.path + (("?" + p.query) if p.query else "")
    else:
        url = h
    print("--- FETCH", url)
    r2 = c.get(url)
    ct = r2.get("Content-Type")
    body = r2.content[:180]
    print(" status", r2.status_code, "CT", ct)
    print(" start", body)
    # detect HTML masquerading as CSS
    low = body.lower()
    if b"<html" in low or b"<!doctype" in low or b"<script" in low:
        print(" WARNING: body looks like HTML")
