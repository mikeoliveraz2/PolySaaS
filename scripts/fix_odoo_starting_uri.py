"""
Clear starting_uri for Odoo PassThroughEndpoint (local dev fix).

When starting_uri is set to '/web', the sidebar link becomes /pt/admin/localhost:8086/web,
which causes Odoo to show the login page immediately instead of letting the handler
manage the redirect.

This script clears starting_uri to '', so the link is just the bare base
(/pt/admin/localhost:8086/), and the handler can follow Odoo's internal redirect.
"""
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from dose.models import PassThroughEndpoint, Tenant

print("Clearing Odoo starting_uri...")

# Fix public schema
with connection.cursor() as c:
    c.execute('SET search_path TO public')

odoo_ep = PassThroughEndpoint.objects.filter(slug='odoo').first()
if odoo_ep:
    print(f'  PUBLIC: {odoo_ep.starting_uri!r} -> ""')
    odoo_ep.starting_uri = ''
    odoo_ep.save()
else:
    print('  PUBLIC: no odoo endpoint found')

# Fix all tenant schemas
for tenant in Tenant.objects.exclude(schema_name='public'):
    with connection.cursor() as c:
        c.execute(f'SET search_path TO "{tenant.schema_name}"')
    
    odoo_ep = PassThroughEndpoint.objects.filter(slug='odoo').first()
    if odoo_ep:
        print(f'  {tenant.schema_name}: {odoo_ep.starting_uri!r} -> ""')
        odoo_ep.starting_uri = ''
        odoo_ep.save()

print("\n✅ Done. Restart PolySaaS and test Odoo link.")
