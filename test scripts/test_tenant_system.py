#!/usr/bin/env python
"""
Test script for session-based tenant system
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

def test_imports():
    """Test that all our models can be imported"""
    try:
        from dose.models import Tenant, UserProfile, TenantAwareModel
        print("✅ Successfully imported Tenant models")
        return True
    except ImportError as e:
        print(f"❌ Failed to import models: {e}")
        return False

def test_database_connection():
    """Test database connectivity"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result[0] == 1:
                print("✅ Database connection successful")
                return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_models():
    """Test model operations"""
    try:
        from dose.models import Tenant
        # Test creating a tenant
        tenant_count = Tenant.objects.count()
        print(f"✅ Found {tenant_count} existing tenants")
        return True
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def test_views():
    """Test that views can be imported"""
    try:
        from dose.views import (
            index, login_view, dashboard, 
            get_current_tenant, setup_demo_view
        )
        print("✅ Successfully imported view functions")
        return True
    except ImportError as e:
        print(f"❌ Failed to import views: {e}")
        return False

def test_urls():
    """Test URL configuration"""
    try:
        from django.urls import reverse
        # Test a few key URLs
        urls_to_test = [
            'dose:index',
            'dose:login', 
            'dose:dashboard',
            'dose:debug',
            'dose:setup_demo'
        ]
        
        for url_name in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"✅ URL {url_name} -> {url}")
            except Exception as e:
                print(f"❌ URL {url_name} failed: {e}")
                return False
        return True
    except Exception as e:
        print(f"❌ URL test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Session-based Tenant System")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_database_connection,
        test_models,
        test_views,
        test_urls
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Session-based tenant system is ready.")
        print("\nNext steps:")
        print("1. Run: python manage.py migrate")
        print("2. Visit: http://localhost:8000/dose/setup-demo/")
        print("3. Login at: http://localhost:8000/dose/login/")
        print("4. Use credentials: demouser/demo123")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")

if __name__ == '__main__':
    main()
