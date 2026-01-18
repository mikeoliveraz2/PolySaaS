#!/usr/bin/env python
import os
import django
from django.core.management import call_command

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from dose.models import Tenant

SCHEMA_NAME = 'alpha'

print(f"=== Running migrations for schema: {SCHEMA_NAME} ===")

try:
    tenant = Tenant.objects.get(schema_name=SCHEMA_NAME)
    print(f"✓ Tenant found: {tenant}")
except Tenant.DoesNotExist:
    print(f"ERROR: Tenant with schema_name '{SCHEMA_NAME}' does not exist.")
    exit(1)

# Switch to tenant schema and run migrations
from django.db import connection
print(f"Setting search_path to schema '{SCHEMA_NAME}'...")
with connection.cursor() as cursor:
    cursor.execute(f"SET search_path TO {SCHEMA_NAME},public;")
    print(f"Running migrations in schema '{SCHEMA_NAME}'...")
    call_command('migrate', verbosity=1)
    print(f"✓ Migrations completed for schema '{SCHEMA_NAME}'")

print("=== DONE ===")
