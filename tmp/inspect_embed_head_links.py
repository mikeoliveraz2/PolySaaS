import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

c = Client()
c.force_login(get_user_model().objects.get(username__iexact="olientadmin"))
s = c.session
s["tenant_slug"] = "olient"
s.save()

html = c.get("/pt/admin/app.hubspot.com/home/").content.decode("utf-8", errors="replace")

start = html.find("Upstream head first")
chunk = html[start : start + 80000] if start >= 0 else html[:80000]
links = re.findall(r"<link[^>]+>", chunk, re.I)
print("links in embed_head chunk:", len(links))
for link in links:
    low = link.lower()
    if "stylesheet" in low or "hsappstatic" in low:
        print(link[:280])

bm = re.search(r'class="polysaas-passthrough-scope"[^>]*>(.{0,800})', html, re.S)
print("\nscope body start:")
print(bm.group(1)[:500] if bm else "NOT FOUND")

# Check if CSS is ONLY after block.super (Jazzmin) - wrong order
shield = html.find("polysaas-passthrough-embed-shield")
first_hs_css = html.find("static.hsappstatic.net")
print(f"\nfirst hsappstatic at {first_hs_css}, shield style at {shield}")
print("CSS before shield:", first_hs_css < shield if first_hs_css >= 0 and shield >= 0 else "n/a")
