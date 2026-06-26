"""Simulate passthrough sidebar resolution for a tenant schema."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection
from dose.models import Tenant, TenantApp
from dose.models.pass_through_endpoint import PassThroughEndpoint
from dose.middleware.jazzmin_tenant_theme import _endpoint_to_app_name

schema = "polysaasppd"
tenant = Tenant.objects.filter(schema_name=schema).first()
print(f"Tenant: {tenant.name} ({tenant.slug})")

with connection.cursor() as cursor:
    cursor.execute(f'SET search_path TO "{schema}",public;')

all_eps = list(
    PassThroughEndpoint.objects.filter(show_in_menu=True)
    .exclude(menu_title__isnull=True)
    .exclude(menu_title__exact="")
)
print(f"\nPassThroughEndpoint rows (show_in_menu): {len(all_eps)}")

visible = []
for ep in all_eps:
    app_name = _endpoint_to_app_name(ep)
    ta = None
    if app_name:
        ta = TenantApp.public_bundles.filter(
            tenant=tenant, app_name=app_name
        ).first()
    ok = ta and ta.status == "active"
    print(
        f"  {'+' if ok else '-'} {ep.menu_title}: app={app_name!r} "
        f"TenantApp={getattr(ta, 'status', None)}"
    )
    if ok:
        visible.append(ep)

print(f"\nSidebar should show {len(visible)} PASSTHROUGH SERVICES cards:")
for ep in visible:
    host = (ep.endpoint_url or "").split("//")[-1].split("/")[0]
    print(f"  - {ep.menu_title} -> /pt/admin/{host}/")
