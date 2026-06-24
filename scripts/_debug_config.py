import os, sys, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
sys.path.insert(0, "D:/PolySaaS")
django.setup()
from django.contrib.auth import get_user_model
from django.test import Client
User = get_user_model()
c = Client()
c.force_login(User.objects.filter(is_staff=True).first())
r = c.get("/dose/sniff/2/native/api/v4/config/client")
print(r.status_code)
print(r.content.decode())
