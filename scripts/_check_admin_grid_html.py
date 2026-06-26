"""Inspect admin-main-wrapper DOM from rendered /admin/ HTML."""
import os
import re
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()
user = User.objects.filter(username="polysaast142").first() or User.objects.filter(is_superuser=True).first()
client = Client()
client.force_login(user)
response = client.get("/admin/")
html = response.content.decode("utf-8", "replace")

print("user:", user.username)
print("status:", response.status_code)
print("inner admin-content-grid div:", '<div class="admin-content-grid">' in html)
print("minmax grid css:", "minmax(0, 1fr)" in html)

wrap = re.search(r'<div class="admin-main-wrapper">\s*<div class="collapsible-nav"', html)
sibling = re.search(
    r'</div>\s*<!-- End sidebar column -->\s*<div class="dose-content-col">',
    html,
)
print("wrapper then sidebar:", bool(wrap))
print("sidebar closed before dose-content-col:", bool(sibling))
print(
    "link inside wrapper:",
    bool(
        re.search(
            r'<div class="admin-main-wrapper">[\s\S]{0,200}<link href="https://fonts.googleapis.com/icon',
            html,
        )
    ),
)
print("material icons link in head area:", html.find("Material+Icons") < html.find("admin-main-wrapper"))
