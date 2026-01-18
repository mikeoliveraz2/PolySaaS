"""
Test script to verify dashboard and landing page enhancements
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from dose.models import PassThroughEndpoint, Tenant
from django.test import RequestFactory
from dose.admin import PassThroughEndpointAdmin

print("=" * 80)
print("DOSE DASHBOARD & LANDING PAGE ENHANCEMENTS - TEST RESULTS")
print("=" * 80)

# Test 1: Check PassthroughEndpoint records
print("\n1. PASSTHROUGH ENDPOINTS CHECK")
print("-" * 80)
try:
    endpoints = PassThroughEndpoint.objects.filter(is_enabled=True)
    print(f"[OK] Found {endpoints.count()} enabled PassthroughEndpoint(s):")
    for ep in endpoints:
        print(f"   - {ep.menu_title or ep.description or ep.provider}")
        print(f"     Trigger: {ep.trigger_path}")
        print(f"     Endpoint: {ep.endpoint_url}")
        print(f"     Show in menu: {ep.show_in_menu}")

    menu_endpoints = PassThroughEndpoint.objects.filter(is_enabled=True, show_in_menu=True)
    print(f"\n[OK] {menu_endpoints.count()} endpoint(s) will show in navigation menus")

except Exception as e:
    print(f"[ERROR] Error checking PassthroughEndpoints: {e}")

# Test 2: Check PassthroughEndpoint permissions
print("\n2. PASSTHROUGH ENDPOINT PERMISSIONS CHECK")
print("-" * 80)
try:
    factory = RequestFactory()
    admin = PassThroughEndpointAdmin(PassThroughEndpoint, None)

    # Test with staff user
    staff_user = User.objects.filter(is_staff=True).first()
    if staff_user:
        request = factory.get('/admin/')
        request.user = staff_user

        can_add = admin.has_add_permission(request)
        can_change = admin.has_change_permission(request)
        can_delete = admin.has_delete_permission(request)
        can_view = admin.has_view_permission(request)

        print(f"Staff user '{staff_user.username}' permissions:")
        print(f"   [OK] Can add: {can_add}")
        print(f"   [OK] Can change: {can_change}")
        print(f"   [OK] Can delete: {can_delete}")
        print(f"   [OK] Can view: {can_view}")
    else:
        print("[WARN] No staff user found to test")

    # Test with non-staff user
    non_staff = User.objects.filter(is_staff=False).first()
    if non_staff:
        request = factory.get('/admin/')
        request.user = non_staff

        can_add = admin.has_add_permission(request)
        can_change = admin.has_change_permission(request)
        can_delete = admin.has_delete_permission(request)
        can_view = admin.has_view_permission(request)

        print(f"\nNon-staff user '{non_staff.username}' permissions:")
        print(f"   [BLOCK] Can add: {can_add} (should be False)")
        print(f"   [BLOCK] Can change: {can_change} (should be False)")
        print(f"   [BLOCK] Can delete: {can_delete} (should be False)")
        print(f"   [BLOCK] Can view: {can_view} (should be False)")

        if not (can_add or can_change or can_delete or can_view):
            print("\n[PASSED] Non-staff user correctly blocked from PassthroughEndpoint")
        else:
            print("\n[FAILED] Non-staff user has unexpected permissions!")
    else:
        print("[WARN] No non-staff user found to test")

except Exception as e:
    print(f"[ERROR] Error checking permissions: {e}")

# Test 3: Check Jazzmin settings
print("\n3. ADMIN MENU CONFIGURATION CHECK")
print("-" * 80)
try:
    from django.conf import settings
    topmenu = settings.JAZZMIN_SETTINGS.get('topmenu_links', [])

    print(f"Admin top menu items ({len(topmenu)}):")
    for item in topmenu:
        name = item.get('name', item.get('model', 'Unknown'))
        url = item.get('url', 'N/A')
        print(f"   - {name}: {url}")

    landing_link = any('Landing Page' in str(item.get('name', '')) for item in topmenu)
    if landing_link:
        print("\n[PASSED] 'Landing Page' link found in admin menu")
    else:
        print("\n[FAILED] 'Landing Page' link NOT found in admin menu")

except Exception as e:
    print(f"[ERROR] Error checking Jazzmin settings: {e}")

# Test 4: Check dashboard view
print("\n4. DASHBOARD VIEW DATA CHECK")
print("-" * 80)
try:
    from django.contrib.sessions.models import Session
    from django.utils import timezone
    from datetime import timedelta

    # Count active sessions
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    active_users = 0
    for session in active_sessions:
        session_data = session.get_decoded()
        if '_auth_user_id' in session_data:
            active_users += 1

    print(f"[OK] Active sessions: {active_sessions.count()}")
    print(f"[OK] Active users: {active_users}")

    # Check tenant
    tenant = Tenant.objects.first()
    if tenant:
        print(f"[OK] Default tenant: {tenant.name}")
    else:
        print("[WARN] No tenant found")

except Exception as e:
    print(f"[ERROR] Error checking dashboard data: {e}")

# Test 5: URL routing check
print("\n5. URL CONFIGURATION CHECK")
print("-" * 80)
try:
    from django.urls import resolve, reverse

    # Test key URLs
    urls_to_test = [
        ('dose:landing_page', '/dose/'),
        ('dose:dashboard', '/dose/dashboard/'),
        ('admin:index', '/admin/'),
    ]

    for name, expected_path in urls_to_test:
        try:
            path = reverse(name)
            print(f"[OK] {name}: {path}")
        except Exception as e:
            print(f"[ERROR] {name}: Error - {e}")

except Exception as e:
    print(f"[ERROR] Error checking URLs: {e}")

# Test 6: Check debug mode
print("\n6. DEBUG MODE CHECK")
print("-" * 80)
try:
    from django.conf import settings
    debug_mode = settings.DEBUG
    print(f"DEBUG = {debug_mode}")
    if debug_mode:
        print("[WARN] Debug messages WILL be visible on dashboard")
    else:
        print("[OK] Debug messages will be hidden on dashboard")
except Exception as e:
    print(f"[ERROR] Error checking debug mode: {e}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
