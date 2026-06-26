"""Inspect dose-content-col inner structure on /admin/."""
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

m = re.search(r'<div class="dose-content-col">(.*)</div>\s*</div>\s*(?:<footer|</section)', html, re.S)
if not m:
    m = re.search(r'<div class="dose-content-col">(.{0,8000})', html, re.S)
content = m.group(1) if m else ""
print("content length", len(content))
print("col-md-6 count", content.count("col-md-6"))
print("col-lg-6 count", content.count("col-lg-6"))
print("row count", content.count('class="row'))
print("first 1500 chars:")
print(content[:1500])

# wrapper parent chain
idx = html.find('class="dose-content-col"')
print("\nancestors snippet:")
print(html[max(0, idx - 800) : idx + 50])
