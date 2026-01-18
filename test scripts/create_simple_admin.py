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

# Create a simple admin user with known credentials
try:
    # Delete existing user if exists
    try:
        existing_user = TenantUser.objects.get(username='admin')
        existing_user.delete()
        print("Deleted existing admin user")
    except TenantUser.DoesNotExist:
        pass
    
    # Create new admin user
    admin_user = TenantUser.objects.create_superuser(
        username='admin',
        email='admin@localhost.com',
        password='admin123'
    )
    
    print("Created new admin user:")
    print(f"  Username: {admin_user.username}")
    print(f"  Email: {admin_user.email}")
    print(f"  Password: admin123")
    print(f"  Staff: {admin_user.is_staff}")
    print(f"  Superuser: {admin_user.is_superuser}")
    print(f"  Active: {admin_user.is_active}")
    
except Exception as e:
    print(f"Error creating admin user: {e}")

print("\nTry logging in at: http://localhost:8000/admin/")
print("Username: admin")
print("Password: admin123")
