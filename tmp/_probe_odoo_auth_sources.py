"""Auth probe using endpoint + settings defaults. No secrets printed."""
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()
from django.conf import settings
from django.db import connection
from dose.models.pass_through_endpoint import PassThroughEndpoint
from dose.models import Tenant, TenantApp
from dose.services.odoo_rpc import OdooRpcClient, OdooRpcError

print("settings_db", getattr(settings, "ODOO_SHARED_DB", None))
print("settings_url", getattr(settings, "ODOO_SHARED_URL", None))

eps = list(PassThroughEndpoint.objects.filter(is_enabled=True))
print("endpoint_count", len(eps))
for ep in eps:
    url = (ep.endpoint_url or "").lower()
    if "8086" in url or "odoo" in url or (ep.slug or "").lower() == "odoo":
        print(
            "ep",
            "id", ep.id,
            "slug", ep.slug,
            "url", ep.endpoint_url,
            "has_user", bool(ep.auth_username),
            "has_pass", bool(ep.auth_password),
            "user_set", bool((ep.auth_username or "").strip()),
        )

# TenantApp odoo rows across known schemas (keys only)
from dose.models import Tenant
tenants = list(Tenant.objects.all()[:20])
print("tenant_count", len(tenants))
for t in tenants:
    schema = t.schema_name or t.slug
    try:
        with connection.cursor() as cur:
            cur.execute(f'SET search_path TO "{schema}", public;')
        ta = TenantApp.objects.filter(app_name="odoo").first()
        extra = ta.extra_config if ta and isinstance(ta.extra_config, dict) else {}
        print(
            "tenant", schema,
            "has_odoo", bool(ta),
            "odoo_db", extra.get("odoo_db"),
            "odoo_url", extra.get("odoo_url"),
            "login", extra.get("odoo_login"),
            "has_password", bool(extra.get("odoo_password")),
        )
    except Exception as e:
        print("tenant_err", schema, type(e).__name__)

# Try settings DB + admin/admin (local docker default) — print only ok/fail
for db in ("odoo", "odoo_odoo2", "odoo_test_master"):
    client = OdooRpcClient(
        url=getattr(settings, "ODOO_SHARED_URL", "http://localhost:8086"),
        db=db,
        username="admin",
        password="admin",
    )
    try:
        uid = client.authenticate()
        print("admin_admin_OK", db, "uid", uid, "transport", client.transport)
    except OdooRpcError as e:
        print("admin_admin_FAIL", db, e.status)
