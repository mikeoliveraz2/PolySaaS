"""One-off: delete public mis-placed instructions and re-provision in tenant schema."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from dose.models import Tenant
from dose.services.odoo_orchestration_provisioner import provision_odoo_invoicing_orchestration

tenant = Tenant.objects.get(slug='polysaasppd')
with connection.cursor() as c:
    c.execute("DELETE FROM public.dose_instruction WHERE tenant_slug = %s", [tenant.slug])
    print(f"Deleted {c.rowcount} row(s) from public.dose_instruction")

result = provision_odoo_invoicing_orchestration(tenant)
print('Provision result:', result)

with connection.cursor() as c:
    c.execute('SELECT COUNT(*) FROM polysaasppd.dose_instruction')
    print('polysaasppd.dose_instruction count:', c.fetchone()[0])
    c.execute('SELECT COUNT(*) FROM public.dose_instruction WHERE tenant_slug = %s', [tenant.slug])
    print('public.dose_instruction count for tenant:', c.fetchone()[0])
    c.execute(
        'SELECT id, requestpath, executescript FROM polysaasppd.dose_instruction ORDER BY id'
    )
    for row in c.fetchall():
        print(' ', row)
