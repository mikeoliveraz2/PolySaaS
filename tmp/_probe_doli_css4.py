"""Inspect wrapped Dolibarr page for CSP and body-class / link placement."""
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

r = c.get(PREFIX + "/admin/company.php?mainmenu=home&leftmenu=setup", follow=True)
html = r.content.decode("utf-8", "replace")
print("headers CSP:", r.get("Content-Security-Policy"))
print("X-CTO:", r.get("X-Content-Type-Options"))

# Where do doli stylesheets sit?
for i, m in enumerate(re.finditer(r'<link[^>]+stylesheet[^>]+>', html, re.I)):
    pos = m.start()
    ctx = html[max(0, pos - 80) : pos + 40]
    print(f"LINK@{pos} near: {re.sub(chr(10), ' ', ctx)[:120]}")

body_m = re.search(r"<body([^>]*)>", html, re.I)
print("BODY attrs:", (body_m.group(1)[:200] if body_m else None))

# Are Dolibarr menu ids present?
for needle in ("id-top", "id-left", "mainmenu", "side-nav", "tmenu", "eldy"):
    print(f" has {needle}:", needle in html)

# Count how many style.css.php and whether inside head vs after body
head = re.search(r"<head[^>]*>(.*?)</head>", html, re.I | re.S)
if head:
    hc = head.group(1)
    print("in HEAD style.css.php:", "style.css.php" in hc)
    print("in HEAD jquery-ui:", "jquery-ui.css" in hc)
print("embed_head marker / pt theme count:", html.count("/theme/eldy/style.css.php"))

# Save a snippet for inspection
open("tmp/_doli_company_head_snip.html", "w", encoding="utf-8").write(html[:8000])
print("wrote tmp/_doli_company_head_snip.html")
