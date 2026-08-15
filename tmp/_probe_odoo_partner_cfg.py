import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()
from django.db import connection
from django.conf import settings
from dose.models import TenantApp
from urllib.parse import urlparse
import requests

print("ODOO_SHARED_URL", getattr(settings, "ODOO_SHARED_URL", None))
print("ODOO_SHARED_DB", getattr(settings, "ODOO_SHARED_DB", None))

with connection.cursor() as cur:
    cur.execute('SET search_path TO "pso17", public;')
tas = list(TenantApp.objects.filter(app_name="odoo"))
print("pso17 TenantApp odoo count", len(tas))
for ta in tas:
    extra = ta.extra_config if isinstance(ta.extra_config, dict) else {}
    keys = sorted(extra.keys())
    print("extra_keys", keys)
    print("has_login", bool(extra.get("odoo_login")))
    print("has_password", bool(extra.get("odoo_password")))
    print("odoo_url", extra.get("odoo_url"))
    print("odoo_db", extra.get("odoo_db"))
    print("has_uid", extra.get("odoo_uid") is not None)

url = getattr(settings, "ODOO_SHARED_URL", "http://localhost:8086")
try:
    r = requests.get(url, timeout=5, allow_redirects=False)
    print("odoo_http", r.status_code)
except Exception as e:
    print("odoo_http_err", type(e).__name__)
