import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django
django.setup()

from django.test import Client

c = Client()
r = c.get("/accounts/login/")
html = r.content.decode()
print("next field in form:", "name=\"next\"" in html)
r2 = c.get("/admin/login/", follow=False)
print("admin/login redirect:", r2.status_code, r2.get("Location"))
from dose.account_adapter import CustomAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()
u = User.objects.filter(username__iexact="olientAdmin").first()
if u:
    from django.test import RequestFactory
    req = RequestFactory().get("/accounts/login/?next=/admin/")
    req.user = u
    url = CustomAccountAdapter().get_login_redirect_url(req)
    print("adapter redirect (with ?next=/admin/):", url)
