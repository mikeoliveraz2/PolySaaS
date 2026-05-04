import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django
django.setup()
from django.db import connection
from dose.models import NavigationPanel, Tenant

for t in Tenant.objects.all():
    schema = t.schema_name
    print(f'Tenant: {t.name} (schema: {schema})')
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{schema}",public;')
            count = NavigationPanel.objects.count()
            print(f'  NavigationPanel count: {count}')
            for p in NavigationPanel.objects.all():
                print(f'    - {p.title} (tenant={p.tenant_id}, active={p.is_active})')
    except Exception as e:
        print(f'  Error: {e}')

print('\nPublic schema:')
with connection.cursor() as cursor:
    cursor.execute('SET search_path TO public;')
    count = NavigationPanel.objects.count()
    print(f'  NavigationPanel count: {count}')
    for p in NavigationPanel.objects.all():
        print(f'    - {p.title} (tenant={p.tenant_id}, active={p.is_active})')
