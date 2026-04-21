#!/usr/bin/env python
import os
import sys
import django
from django.core.management import call_command

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django_tenants.utils import schema_context
from dose.models import Tenant
from django.db import connection

try:
    # Get the demo tenant
    demo_tenant = Tenant.objects.get(schema_name='demo')
    print(f"Found demo tenant: {demo_tenant}")
    
    # Skip making migrations for dose app to avoid the TenantUser issue
    print("Running shared migrations only...")
    call_command('migrate_schemas', '--shared', verbosity=2)
    
    # Force migration for demo tenant specifically, but only for core Django apps
    print("Running core Django migrations for demo tenant...")
    with schema_context('demo'):
        print("Inside demo schema context, running core migrations...")
        
        # Run only the essential Django migrations
        try:
            call_command('migrate', 'contenttypes', verbosity=2)
            print("✓ contenttypes migrated")
        except Exception as e:
            print(f"contenttypes migration error: {e}")
            
        try:
            call_command('migrate', 'auth', verbosity=2)
            print("✓ auth migrated")
        except Exception as e:
            print(f"auth migration error: {e}")
            
        try:
            call_command('migrate', 'sessions', verbosity=2)
            print("✓ sessions migrated")
        except Exception as e:
            print(f"sessions migration error: {e}")
            
        try:
            call_command('migrate', 'admin', verbosity=2)
            print("✓ admin migrated")
        except Exception as e:
            print(f"admin migration error: {e}")
        
        # Check if auth_user table exists now
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'demo' 
                AND table_name = 'auth_user'
            """)
            auth_user_exists = cursor.fetchone()
            
            if auth_user_exists:
                print("SUCCESS: auth_user table exists in demo schema!")
                from django.contrib.auth.models import User
                user_count = User.objects.count()
                print(f"Demo tenant now has {user_count} users")
            else:
                print("ERROR: auth_user table still doesn't exist!")
                print("Checking what tables do exist in demo schema...")
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'demo'
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                print(f"Tables in demo schema: {[t[0] for t in tables]}")
                
                # Try running migrate without any specific app to apply all pending migrations
                print("Running general migrate...")
                call_command('migrate', verbosity=2)
                
                # Check one more time
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'demo' 
                    AND table_name = 'auth_user'
                """)
                auth_user_exists = cursor.fetchone()
                
                if auth_user_exists:
                    print("SUCCESS: auth_user table now exists!")
                    from django.contrib.auth.models import User
                    user_count = User.objects.count()
                    print(f"Demo tenant now has {user_count} users")
                else:
                    print("FINAL ATTEMPT: Creating auth_user table manually...")
                    # As a last resort, create the table manually
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS auth_user (
                            id SERIAL PRIMARY KEY,
                            password VARCHAR(128) NOT NULL,
                            last_login TIMESTAMP WITH TIME ZONE,
                            is_superuser BOOLEAN NOT NULL,
                            username VARCHAR(150) NOT NULL UNIQUE,
                            first_name VARCHAR(150) NOT NULL,
                            last_name VARCHAR(150) NOT NULL,
                            email VARCHAR(254) NOT NULL,
                            is_staff BOOLEAN NOT NULL,
                            is_active BOOLEAN NOT NULL,
                            date_joined TIMESTAMP WITH TIME ZONE NOT NULL
                        )
                    """)
                    print("Manually created auth_user table")
                    
                    # Also create other essential tables
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
                            content_type_id INTEGER NOT NULL,
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
                    
                    print("Created essential tables manually")
                    
                    # Test if we can now query users
                    try:
                        from django.contrib.auth.models import User
                        user_count = User.objects.count()
                        print(f"SUCCESS: Can now query users! Count: {user_count}")
                    except Exception as e:
                        print(f"Still cannot query users: {e}")
        
except Tenant.DoesNotExist:
    print("Demo tenant not found!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nNext step: Create a superuser for the demo tenant:")
print("python manage.py tenant_command createsuperuser --schema=demo")