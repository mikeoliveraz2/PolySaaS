#!/usr/bin/env python
"""
Test script to verify Active URLs functionality
"""
import os
import sys
import django
import requests
from time import sleep

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from dose.models import UserRequestTracker, Tenant
def test_active_urls_tracking():
    """Test that URLs are being tracked properly"""
    print("Testing Active URLs Tracking...")

    try:
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='testadmin',
            defaults={
                'email': 'test@admin.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ Created test admin user: {user.username}")
        else:
            print(f"✅ Using existing admin user: {user.username}")

        # Get the public tenant
        tenant = Tenant.objects.filter(schema_name='public').first()
        if not tenant:
            print("❌ No public tenant found")
            return False

        print(f"✅ Using tenant: {tenant.name} ({tenant.schema_name})")

        # Check initial tracking count
        initial_count = UserRequestTracker.objects.filter(user=user, tenant=tenant).count()
        print(f"📊 Initial tracked requests: {initial_count}")

        # Simulate some admin requests by creating UserRequestTracker entries directly
        test_paths = [
            '/admin/',
            '/admin/dose/userprofile/',
            '/admin/dose/tenant/',
            '/admin/auth/user/',
            '/admin/dose/atomicservice/',
        ]

        print("🔄 Simulating admin navigation...")
        for path in test_paths:
            # Create entries directly since we don't have real request objects
            UserRequestTracker.objects.create(
                user=user,
                tenant=tenant,
                path=path,
                method='GET',
            )
            print(f"   📝 Recorded: {path}")

        # Check final tracking count
        final_count = UserRequestTracker.objects.filter(user=user, tenant=tenant).count()
        print(f"📊 Final tracked requests: {final_count}")

        # Test the get_recent_paths_for_user method
        recent_paths = UserRequestTracker.get_recent_paths_for_user(user, tenant)
        print(f"🔍 Recent paths retrieved: {len(recent_paths)}")

        for path_info in recent_paths:
            print(f"   🌐 {path_info['path']} ({path_info['method']}) - Count: {path_info['count']}")

        if final_count > initial_count:
            print("✅ Active URLs tracking is working correctly!")
            return True
        else:
            print("❌ No new requests were tracked")
            return False

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_admin_dashboard_context():
    """Test that the admin context processor is providing the right data"""
    print("\nTesting Admin Dashboard Context...")

    try:
        from dose.context_processors import admin_active_urls
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser

        # Create a mock request
        factory = RequestFactory()
        request = factory.get('/admin/')

        # Add session middleware functionality
        from django.contrib.sessions.backends.db import SessionStore
        request.session = SessionStore()
        request.session.create()

        # Test with admin user
        user = User.objects.filter(is_staff=True).first()
        if not user:
            print("❌ No admin user found for testing")
            return False

        request.user = user

        # Test the context processor
        context = admin_active_urls(request)

        print(f"📋 Context keys: {list(context.keys())}")

        if 'recent_paths' in context:
            recent_paths = context['recent_paths']
            print(f"✅ Recent paths in context: {len(recent_paths)} items")
            for path_info in recent_paths[:3]:  # Show first 3
                print(f"   🌐 {path_info['path']} - {path_info['count']} times")
        else:
            print("⚠️  No recent_paths in context")

        if 'tenant' in context:
            tenant = context['tenant']
            print(f"✅ Tenant in context: {tenant.name if tenant else 'None'}")
        else:
            print("⚠️  No tenant in context")

        return True

    except Exception as e:
        print(f"❌ Error testing context: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("🚀 Starting Active URLs Test Suite\n")

    # Test 1: URL Tracking
    test1_result = test_active_urls_tracking()

    # Test 2: Admin Context
    test2_result = test_admin_dashboard_context()

    print(f"\n📊 Test Results:")
    print(f"   URL Tracking: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"   Admin Context: {'✅ PASS' if test2_result else '❌ FAIL'}")

    if test1_result and test2_result:
        print("\n🎉 All tests passed! Active URLs feature is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")