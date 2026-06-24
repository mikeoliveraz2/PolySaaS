import os, sys, re, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
sys.path.insert(0, "D:/PolySaaS")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()
u = User.objects.filter(is_staff=True).first()
print("user", u.username if u else None)
c = Client()
c.force_login(u)
r = c.get("/dose/sniff/2/native/")
print("status", r.status_code)
print("csp", r.get("Content-Security-Policy", "none"))
print("xfo", r.get("X-Frame-Options", "none"))
body = r.content.decode("utf-8", "replace")
print("has shim", "installBasenameLock" in body)
m = re.search(r'src="([^"]*main[^"]*\.js)"', body)
print("main", m.group(1) if m else "no")
# test config client through proxy
r2 = c.get("/dose/sniff/2/native/api/v4/config/client")
print("config status", r2.status_code, "len", len(r2.content))
if r2.status_code == 200:
    print("config snippet", r2.content[:200])
