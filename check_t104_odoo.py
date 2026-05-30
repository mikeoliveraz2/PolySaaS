import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dose.settings')
django.setup()

from dose.models import TenantApp, Tenant

t = Tenant.objects.get(slug='t104')
ta = TenantApp.objects.filter(tenant=t, app_name='odoo').first()

print(f"Tenant: {t.name} (slug={t.slug}, schema={t.schema_name})")
print(f"TenantApp status: {ta.status if ta else 'None'}")
if ta:
    print(f"TenantApp last_error: {ta.last_error}")
    print(f"Extra config keys: {list(ta.extra_config.keys()) if ta.extra_config else []}")
    if ta.extra_config and isinstance(ta.extra_config, dict):
        print(f"  odoo_login: {ta.extra_config.get('odoo_login')}")
        print(f"  odoo_db: {ta.extra_config.get('odoo_db')}")
        print(f"  odoo_url: {ta.extra_config.get('odoo_url')}")
        print(f"  odoo_session_id: {ta.extra_config.get('odoo_session_id', 'None')}")
