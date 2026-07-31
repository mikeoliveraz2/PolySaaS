import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

with connection.cursor() as c:
    c.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema','pg_catalog','public') ORDER BY schema_name")
    schemas = [r[0] for r in c.fetchall()]

print('Schemas:', schemas)

from dose.models import PassThroughEndpoint

for schema in schemas:
    with connection.cursor() as c:
        c.execute(f'SET search_path TO "{schema}",public')
    eps = PassThroughEndpoint.objects.filter(slug='odoo')
    for ep in eps:
        print(f'  [{schema}] slug={ep.slug} endpoint_url={ep.endpoint_url} starting_uri={ep.starting_uri}')
