"""Which local Odoo DB accepts the pso17 TenantApp login? No secrets printed."""
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()
from django.db import connection
from dose.models import TenantApp
from dose.services.odoo_rpc import OdooRpcClient, OdooRpcError, public_config

with connection.cursor() as cur:
    cur.execute('SET search_path TO "pso17", public;')
ta = TenantApp.objects.filter(app_name="odoo").first()
extra = ta.extra_config if isinstance(ta.extra_config, dict) else {}
url = extra.get("odoo_url") or "http://localhost:8086"
login = extra.get("odoo_login") or ""
password = extra.get("odoo_password") or ""
print("login_present", bool(login), "password_present", bool(password), "url", url)

dbs = ["odoo", "odoo_odoo2", "odoo_test_master", extra.get("odoo_db") or ""]
for db in dbs:
    if not db:
        continue
    client = OdooRpcClient(url=url, db=db, username=login, password=password)
    try:
        uid = client.authenticate()
        print("AUTH_OK", db, "uid", uid, "transport", client.transport)
    except OdooRpcError as e:
        print("AUTH_FAIL", db, e.status, str(e)[:180])
    except Exception as e:
        print("AUTH_ERR", db, type(e).__name__, str(e)[:180])
