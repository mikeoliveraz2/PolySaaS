#!/usr/bin/env python
import os
import sys
import django
from django.core.management import call_command

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

## Removed django-tenants dependency
from dose.models import Tenant
from django.db import connection

try:
    # Get the demo tenant
    demo_tenant = Tenant.objects.get(schema_name='demo')
    print(f"Found demo tenant: {demo_tenant}")
    
    # First, make sure we have all migrations created
    print("Creating any missing migrations...")
    call_command('makemigrations', verbosity=2)
    
    # Create migrations specifically for dose app if needed
    print("Creating migrations for dose app...")
    call_command('makemigrations', 'dose', verbosity=2)
    
    # Run shared migrations first
    print("Running shared migrations...")
    call_command('migrate_schemas', '--shared', verbosity=2)
    
    # Force migration for demo tenant specifically
    print("Running migrations specifically for demo tenant...")
    with schema_context('demo'):
        print("Inside demo schema context, running migrate...")
        call_command('migrate', verbosity=2)
        
        # Check if tables exist
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
                """)
                tables = cursor.fetchall()
                print(f"Tables in demo schema: {[t[0] for t in tables]}")
                
                # Force create auth tables
                print("Forcing creation of auth tables...")
                call_command('migrate', 'auth', verbosity=2)
                call_command('migrate', 'contenttypes', verbosity=2)
                call_command('migrate', 'sessions', verbosity=2)
                call_command('migrate', 'admin', verbosity=2)
                
                # Check again
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'demo' 
                    AND table_name = 'auth_user'
                """)
                auth_user_exists = cursor.fetchone()
                
                if auth_user_exists:
                    print("SUCCESS: auth_user table now exists after forced migration!")
                    from django.contrib.auth.models import User
                    user_count = User.objects.count()
                    print(f"Demo tenant now has {user_count} users")
                else:
                    print("STILL FAILED: Cannot create auth_user table")
        
except Tenant.DoesNotExist:
    print("Demo tenant not found. Creating it...")
    demo_tenant = Tenant.objects.create(
        schema_name='demo',
        name='Demo Tenant',
        tagline='Demo Environment'
    )
    print(f"Created demo tenant: {demo_tenant}")
    
    # Create domain
    from dose.models import Domain
    demo_domain = Domain.objects.create(
        domain='localhost',
        tenant=demo_tenant,
        is_primary=True
    )
    print(f"Created demo domain: {demo_domain}")
    
    # Run migrations for new tenant
    with schema_context('demo'):
        print("Running migrations for new demo tenant...")
        call_command('migrate', verbosity=2)
        print("New demo tenant setup completed!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nNext step: Create a superuser for the demo tenant:")
print("python manage.py tenant_command createsuperuser --schema=demo")
