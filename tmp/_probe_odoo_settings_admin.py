"""Auth with settings XML-RPC admin against ODOO_SHARED_DB. No secrets printed."""
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()
from django.conf import settings
from dose.services.odoo_rpc import OdooRpcClient, OdooRpcError, public_config

config = {
    "url": str(getattr(settings, "ODOO_SHARED_URL", "") or "").rstrip("/"),
    "db": str(getattr(settings, "ODOO_SHARED_DB", "") or ""),
    "username": str(getattr(settings, "ODOO_XMLRPC_ADMIN_LOGIN", "") or ""),
    "password": str(getattr(settings, "ODOO_XMLRPC_ADMIN_PASSWORD", "") or ""),
}
print("public", public_config(config))
client = OdooRpcClient.from_config(config)
try:
    uid = client.authenticate()
    print("AUTH_OK uid", uid, "transport", client.transport)
except OdooRpcError as e:
    print("AUTH_FAIL", e.status, str(e)[:200])
