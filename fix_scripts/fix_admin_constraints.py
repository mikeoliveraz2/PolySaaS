#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/c/Users/michael.oliver/Documents/Dose/DoseV3Master')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import connection

def check_admin_log_constraints():
    """Check and fix admin log foreign key issues"""
    
    print("Checking django_admin_log constraints...")
    
    with connection.cursor() as cursor:
        # Check foreign key constraints on django_admin_log
        cursor.execute("""
            SELECT conname, conrelid::regclass, confrelid::regclass 
            FROM pg_constraint 
            WHERE conrelid = 'django_admin_log'::regclass 
            AND contype = 'f';
        """)
        constraints = cursor.fetchall()
        
        print(f"Found {len(constraints)} foreign key constraints:")
        for constraint in constraints:
            print(f"  - {constraint[0]}: {constraint[1]} -> {constraint[2]}")
        
        # Check if there are invalid user references
        cursor.execute("""
            SELECT DISTINCT user_id 
            FROM django_admin_log 
            WHERE user_id NOT IN (SELECT id FROM auth_user);
        """)
        invalid_users = cursor.fetchall()
        
        if invalid_users:
            print(f"Found {len(invalid_users)} invalid user references in admin log:")
            for user_id in invalid_users:
                print(f"  - User ID: {user_id[0]}")
            
            # Clean up invalid admin log entries
            cursor.execute("""
                DELETE FROM django_admin_log 
                WHERE user_id NOT IN (SELECT id FROM auth_user);
            """)
            print("Cleaned up invalid admin log entries")
        else:
            print("No invalid user references found")
        
        # Check for any references to dose_tenantuser table
        cursor.execute("""
            SELECT conname, conrelid::regclass, confrelid::regclass 
            FROM pg_constraint 
            WHERE confrelid::regclass::text LIKE '%tenantuser%';
        """)
        tenant_constraints = cursor.fetchall()
        
        if tenant_constraints:
            print(f"Found {len(tenant_constraints)} constraints referencing tenantuser:")
            for constraint in tenant_constraints:
                print(f"  - {constraint[0]}: {constraint[1]} -> {constraint[2]}")
                # Drop the problematic constraint
                cursor.execute(f"ALTER TABLE {constraint[1]} DROP CONSTRAINT {constraint[0]};")
                print(f"    Dropped constraint {constraint[0]}")

if __name__ == "__main__":
    check_admin_log_constraints()
    print("Done!")
