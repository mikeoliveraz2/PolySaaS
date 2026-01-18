#!/usr/bin/env python
import os
import django
from django.core.management import call_command
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant

SCHEMA_NAME = input("Enter tenant schema name (e.g. 'alpha'): ").strip()

print(f"=== Creating schema and tables for tenant: {SCHEMA_NAME} ===")

# Step 1: Create schema if not exists
with connection.cursor() as cursor:
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};")
    print(f"✓ Schema '{SCHEMA_NAME}' ensured.")

# Step 2: Set search_path to new schema
with connection.cursor() as cursor:
    cursor.execute(f"SET search_path TO {SCHEMA_NAME},public;")
    print(f"✓ search_path set to '{SCHEMA_NAME},public'.")

# Step 3: Run migrations to create tables in new schema
print(f"Running migrations in schema '{SCHEMA_NAME}'...")
call_command('migrate', verbosity=1)
print(f"✓ Migrations completed for schema '{SCHEMA_NAME}'")

print("=== DONE ===")
