#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import TenantUser
from django.db import connection

# Set schema to public
connection.set_schema_to_public()

# Check current users
users = TenantUser.objects.all()
print("Current users in public schema:")
for user in users:
    print(f"  {user.username} - Staff: {user.is_staff}, Superuser: {user.is_superuser}, Active: {user.is_active}")

# Fix the publicadmin user if it exists
try:
    user = TenantUser.objects.get(username='publicadmin')
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.save()
    print(f"\nFixed user: {user.username}")
    print(f"  - is_staff: {user.is_staff}")
    print(f"  - is_superuser: {user.is_superuser}")
    print(f"  - is_active: {user.is_active}")
except TenantUser.DoesNotExist:
    print("\nUser 'publicadmin' not found. Creating new admin user...")
    user = TenantUser.objects.create_superuser(
        username='admin',
        email='admin@localhost.com',
        password='admin123'
    )
    print(f"Created new superuser: {user.username}")
