#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from django.conf import settings

# Get database config
db_config = settings.DATABASES['default']
print("Database Configuration:")
print(f"  Engine: {db_config.get('ENGINE')}")
print(f"  Host:   {db_config.get('HOST')}")
print(f"  Port:   {db_config.get('PORT')}")
print(f"  Name:   {db_config.get('NAME')}")
print(f"  User:   {db_config.get('USER')}")

# Test connection
print("\nTesting connection...")
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✓ Connected! PostgreSQL version: {version[0][:80]}")
except Exception as e:
    print(f"✗ Connection failed: {e}")
