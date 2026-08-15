"""Staff-client probe: sniff Files HTML rewrite + CSS status. No secrets printed."""
import os
import re

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.db import connection

User = get_user_model()
user = User.objects.filter(username__iexact="ODOO2").first()
if user is None:
    user = User.objects.filter(is_staff=True).first()
print("user", user.username if user else None, "staff", bool(user and user.is_staff))

client = Client()
client.force_login(user)
session = client.session
session["tenant_slug"] = "pso17"
session.save()

# Bind tenant schema like middleware
with connection.cursor() as c:
    c.execute("SET search_path TO pso17, public")

html_resp = client.get("/pt/polysniff/3/apps/files/", follow=False)
print("FILES status", html_resp.status_code, "ct", html_resp.get("Content-Type", "")[:60], "len", len(html_resp.content))
if html_resp.status_code in (301, 302, 303):
    print("redirect", html_resp.get("Location", "")[:160])

body = html_resp.content.decode("utf-8", errors="ignore")
print("has sudo form", "confirm your password" in body.lower())
print("has shim", "data-polysaas-nc-shim" in body)
print("has prefixed core css", "/pt/polysniff/3/core/css/" in body)
print("has bare /core/css/", bool(re.search(r'href=["\']/core/css/', body)))
print("has prefixed dist", "/pt/polysniff/3/dist/" in body)
print("has bare /dist/", bool(re.search(r'(?:src|href)=["\']/dist/', body)))

css_hrefs = re.findall(r'href=["\']([^"\']+\.css[^"\']*)["\']', body, re.I)[:8]
print("css sample:")
for u in css_hrefs:
    print(" ", u[:140])

# Fetch first prefixed stylesheet if present
target = None
for u in css_hrefs:
    if u.startswith("/pt/polysniff/3/") and ".css" in u:
        target = u.replace("&amp;", "&")
        break
if target:
    css_resp = client.get(target)
    print("CSS GET", target[:90], "->", css_resp.status_code, css_resp.get("Content-Type", "")[:50], "len", len(css_resp.content))
else:
    print("NO prefixed css href to fetch")
