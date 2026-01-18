#!/usr/bin/env python
"""
Test tenant filtering in different contexts
"""
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant
from django.db import connection

def test_tenant_filtering():
    """Test how tenant filtering works"""
    from django.db import connection as db_connection
    
    print(f"Current schema: {getattr(db_connection, 'schema_name', 'unknown')}")
    
    # Test normal queryset
    tenants = Tenant.objects.all()
    print(f"\nNormal queryset count: {tenants.count()}")
    for tenant in tenants:
        print(f"  - {tenant.name} ({tenant.schema_name})")
    
    # Test raw SQL
    try:
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT name, schema_name FROM public.dose_tenant")
            rows = cursor.fetchall()
            print(f"\nRaw SQL count: {len(rows)}")
            for row in rows:
                print(f"  - {row[0]} ({row[1]})")
    except Exception as e:
        print(f"\nRaw SQL failed: {e}")

if __name__ == '__main__':
    test_tenant_filtering()
