import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()
u = User.objects.filter(username="olientAdmin").first() or User.objects.filter(is_staff=True).first()
c = Client()
c.force_login(u)
session = c.session
session["tenant_slug"] = "plysaast10"
session.save()

url = "/dose/sniff/4/native/global-home/246571499"
r = c.get(url)
print("status", r.status_code)
print("content-type", r.get("Content-Type"))
print("x-frame-options", r.get("X-Frame-Options"))
print("csp", r.get("Content-Security-Policy", "")[:80])
print("len", len(r.content))
print("location", r.get("Location"))
body = r.content.decode("utf-8", errors="replace")
print("title", body[body.find("<title"):body.find("</title>")+8] if "<title" in body else "?")
print("frame-ancestors in body", "frame-ancestors" in body.lower())
print("invalid login", "login url is invalid" in body.lower())
