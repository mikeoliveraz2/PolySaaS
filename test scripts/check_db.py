#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection

def check_database():
    cursor = connection.cursor()
    
    print("Current database tables:")
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  {table[0]}")
    
    print("\nChecking for django_admin_log constraints:")
    cursor.execute("""
        SELECT conname, contype, confrelid::regclass as referenced_table 
        FROM pg_constraint 
        WHERE conrelid = 'django_admin_log'::regclass 
        AND contype = 'f';
    """)
    constraints = cursor.fetchall()
    for constraint in constraints:
        print(f"  Constraint: {constraint[0]} -> {constraint[2]}")
    
    print("\nChecking if dose_tenantuser table exists:")
    cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='dose_tenantuser');")
    exists = cursor.fetchone()[0]
    print(f"  dose_tenantuser exists: {exists}")
    
    print("\nChecking if auth_user table exists:")
    cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='auth_user');")
    exists = cursor.fetchone()[0]
    print(f"  auth_user exists: {exists}")

if __name__ == "__main__":
    check_database()
