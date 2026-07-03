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

idx = html.find("Upstream head first")
print("upstream head marker at", idx)
if idx >= 0:
    chunk = html[idx : idx + 4000]
    for line in chunk.splitlines()[:40]:
        if "link" in line.lower() or "script" in line.lower() or "Upstream" in line:
            print(line[:200])

scope = re.search(r'class="polysaas-passthrough-scope"[^>]*>(.{0,1200})', html, re.S | re.I)
print("\nSCOPE BODY START:")
print(scope.group(1)[:800] if scope else "NA")

# Where are hsappstatic link tags relative to </head> and scope?
for i, m in enumerate(re.finditer(r'href="https://static\.hsappstatic\.net[^"]+\.css"', html)):
    pos = m.start()
    before_head_end = html.find("</head>")
    in_head = pos < before_head_end if before_head_end > 0 else False
    print(f"css link {i} pos={pos} in_head={in_head} url={m.group(0)[:100]}")

out = os.path.join(os.path.dirname(__file__), "hs_full_head_sample.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html[:150000])
print("wrote", out, "len", len(html))
