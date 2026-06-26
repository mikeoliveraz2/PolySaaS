"""Inspect /admin/ layout DOM for grid breakage."""
import os
import re

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
import django

django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

user = get_user_model().objects.filter(username="polysaast142").first()
client = Client()
client.force_login(user)
html = client.get("/admin/").content.decode("utf-8", "replace")

idx = html.find("admin-main-wrapper")
print("status ok, wrapper at", idx)
print(html[idx - 250 : idx + 1200])
print("\n=== GRID CHILD SCAN ===")
# Everything between admin-main-wrapper open and dose-content-col
m = re.search(
    r'<div class="admin-main-wrapper[^"]*">(.*?)<div class="dose-content-col">',
    html,
    re.S,
)
if m:
    between = m.group(1)
    print("chars before dose-content-col:", len(between))
    print("script:", between.count("<script"))
    print("style:", between.count("<style"))
    print("link:", between.count("<link"))
    # top-level div closes for sidebar
    print("snippet end:", between[-300:])

# Children of admin-main-wrapper (rough)
m2 = re.search(r'<div class="admin-main-wrapper[^"]*">(.*?)</div>\s*<div class="dose-content-col">', html, re.S)
print("recent-actions in page:", "recent-actions-sidebar" in html)
print("recent-actions-module:", "recent-actions-module" in html)

# Parent row/col
parent = html[max(0, idx - 600) : idx]
for needle in ["container-fluid", "class=\"row", "col-lg", "col-md", "app-content"]:
    if needle in parent:
        print("parent has", needle)
