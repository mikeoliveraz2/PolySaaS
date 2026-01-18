#!/usr/bin/env python
import os
import sys
import django
from django.core.management import call_command

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

## Removed django-tenants dependency
from django.db import connection
from dose.models import Tenant, Domain

print("=== SETTING UP DOMAIN-BASED TENANTS ===")

# Step 1: Create demo tenant
try:
    demo_tenant = Tenant.objects.get(schema_name='demo')
    print(f"✓ Demo tenant exists: {demo_tenant}")
except Tenant.DoesNotExist:
    demo_tenant = Tenant.objects.create(
        schema_name='demo',
        name='Demo Tenant',
        tagline='Demo Environment'
    )
    print(f"✓ Created demo tenant: {demo_tenant}")

# Step 2: Create domain for demo tenant
try:
    demo_domain = Domain.objects.get(domain='demo.localhost')
except Domain.DoesNotExist:
    demo_domain = Domain.objects.create(
        domain='demo.localhost',
        tenant=demo_tenant,
        is_primary=True
    )
    print(f"✓ Created demo domain: {demo_domain}")

# Step 3: Run shared migrations first
print("Running shared migrations...")
call_command('migrate_schemas', '--shared', verbosity=0)
print("✓ Shared migrations completed")

# Step 4: Run tenant migrations and create tables manually if needed
print("Running tenant migrations...")
with schema_context('demo'):
    try:
        # First try normal migrations
        call_command('migrate', verbosity=0)
        print("✓ Demo tenant migrations completed")
    except Exception as e:
        print(f"Migration error: {e}")
        print("Creating auth tables manually...")
        
        # Create auth tables manually
        with connection.cursor() as cursor:
            # Create auth_user table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_user (
                    id SERIAL PRIMARY KEY,
                    password VARCHAR(128) NOT NULL,
                    last_login TIMESTAMP WITH TIME ZONE,
                    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
                    username VARCHAR(150) NOT NULL UNIQUE,
                    first_name VARCHAR(150) NOT NULL DEFAULT '',
                    last_name VARCHAR(150) NOT NULL DEFAULT '',
                    email VARCHAR(254) NOT NULL DEFAULT '',
                    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                )
            """)
            
            # Create other essential tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS django_content_type (
                    id SERIAL PRIMARY KEY,
                    app_label VARCHAR(100) NOT NULL,
                    model VARCHAR(100) NOT NULL,
                    UNIQUE(app_label, model)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_permission (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    content_type_id INTEGER REFERENCES django_content_type(id),
                    codename VARCHAR(100) NOT NULL,
                    UNIQUE(content_type_id, codename)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS django_session (
                    session_key VARCHAR(40) PRIMARY KEY,
                    session_data TEXT NOT NULL,
                    expire_date TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_group (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(150) NOT NULL UNIQUE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_user_groups (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES auth_user(id),
                    group_id INTEGER REFERENCES auth_group(id),
                    UNIQUE(user_id, group_id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_user_user_permissions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES auth_user(id),
                    permission_id INTEGER REFERENCES auth_permission(id),
                    UNIQUE(user_id, permission_id)
                )
            """)
            
            print("✓ Auth tables created manually")
    
    # Create superuser
    try:
        from django.contrib.auth.models import User
        if not User.objects.filter(username='admin').exists():
            user = User.objects.create_superuser(
                username='admin',
                email='admin@demo.com',
                password='admin123'
            )
            print(f"✓ Created superuser: {user.username}")
        else:
            print("✓ Superuser already exists")
        
        user_count = User.objects.count()
        print(f"✓ Demo tenant has {user_count} users")
    except Exception as e:
        print(f"Error creating superuser: {e}")
        print("You may need to create the superuser manually later")

print("\n=== SETUP COMPLETE ===")
print("Next steps:")
print("1. Add to your Windows hosts file (C:\\Windows\\System32\\drivers\\etc\\hosts):")
print("   127.0.0.1 demo.localhost")
print("2. Update ALLOWED_HOSTS in settings.py")
print("3. Remove path-based middleware")
print("4. Access: http://demo.localhost:8000/admin/")
print("5. Login: admin / admin123")

print("\n=== FUTURE PATH-BASED MIGRATION ===")
print("To add path-based routing later, we can add a TENANT_ROUTING_MODE setting.")
