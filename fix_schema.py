#!/usr/bin/env python
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from dose.models import Tenant

# Get tenant
t = Tenant.objects.get(schema_name='polysaast15')
print(f'Found tenant: {t.name} (schema={t.schema_name})')

# Create schema if not exists
with connection.cursor() as c:
    c.execute('SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s', [t.schema_name])
    if c.fetchone():
        print(f'Schema {t.schema_name} already exists')
    else:
        c.execute(f'CREATE SCHEMA IF NOT EXISTS "{t.schema_name}"')
        print(f'Created schema: {t.schema_name}')
