#!/usr/bin/env python
"""
Test Schema Display in D.O.S.E. Headers

This script tests the schema detection functionality we just added.
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from mysite.custom_context_processors import tenant_theme_context
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

def test_schema_detection():
    """Test schema detection functionality"""
    
    print("🔍 Testing Schema Detection for D.O.S.E. Headers")
    print("="*60)
    
    # Test direct database schema detection
    print("1. Direct Database Schema Detection:")
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT current_schema()')
            current_schema = cursor.fetchone()[0]
            print(f"   ✅ Current Database Schema: {current_schema}")
            
            cursor.execute('SELECT version()')
            db_version = cursor.fetchone()[0]
            print(f"   ✅ Database: {db_version[:50]}...")
            
    except Exception as e:
        print(f"   ❌ Error detecting schema: {e}")
    
    print("\n2. Context Processor Testing:")
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/')
    request.user = AnonymousUser()
    
    # Test context processor
    try:
        context = tenant_theme_context(request)
        print(f"   ✅ Context Schema: {context.get('current_schema', 'Not detected')}")
        print(f"   ✅ Schema Display: {context.get('schema_display', 'Not detected')}")
        print(f"   ✅ Tenant Name: {context.get('tenant_name', 'Default')}")
        print(f"   ✅ Tenant Theme: {context.get('tenant_theme', 'Default')}")
        
    except Exception as e:
        print(f"   ❌ Context processor error: {e}")
    
    print("\n3. Available Schemas in Database:")
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                ORDER BY schema_name
            """)
            schemas = cursor.fetchall()
            
            print(f"   📂 Available Schemas ({len(schemas)}):")
            for schema in schemas:
                print(f"      - {schema[0]}")
                
    except Exception as e:
        print(f"   ❌ Error listing schemas: {e}")
    
    print("\n" + "="*60)
    print("🎯 SUMMARY:")
    print("   - Schema detection added to custom_context_processors.py")
    print("   - Admin header updated to show schema information")
    print("   - Main template updated to display schema in tenant info")
    print("   - Schema displayed with icons: 🗄️ Schema | 🔧 DB")
    print("\n🚀 Next Steps:")
    print("   1. Restart Django development server")
    print("   2. Visit admin interface to see schema in header")
    print("   3. Check landing page for schema display")
    print("   4. Test with different tenant contexts")

if __name__ == "__main__":
    test_schema_detection()
