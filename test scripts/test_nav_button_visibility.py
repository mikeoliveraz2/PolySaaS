#!/usr/bin/env python
"""
Test script to diagnose why "Manage My Links" button doesn't appear.
Checks user authentication state and permissions.
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth import get_user_model
from dose.models import Tenant

User = get_user_model()

def test_button_visibility():
    print("=" * 70)
    print("TESTING 'MANAGE MY LINKS' BUTTON VISIBILITY")
    print("=" * 70)

    # Check for non-staff users
    non_staff_users = User.objects.filter(is_staff=False, is_active=True)
    print(f"\n1. Total non-staff users: {non_staff_users.count()}")

    if non_staff_users.exists():
        for user in non_staff_users[:5]:  # Show first 5
            print(f"   - {user.username} (email: {user.email}, is_staff: {user.is_staff}, is_active: {user.is_active})")
    else:
        print("   ⚠️  NO NON-STAFF USERS FOUND!")
        print("   The button condition is: {% if user.is_authenticated and not user.is_staff %}")
        print("   You need a non-staff user to see the button!")

    # Check for staff users
    staff_users = User.objects.filter(is_staff=True, is_active=True)
    print(f"\n2. Total staff users: {staff_users.count()}")

    if staff_users.exists():
        for user in staff_users[:3]:
            print(f"   - {user.username} (is_staff: {user.is_staff}, is_superuser: {user.is_superuser})")

    # Check tenants
    tenants = Tenant.objects.all()
    print(f"\n3. Total tenants: {tenants.count()}")

    if tenants.exists():
        for tenant in tenants[:3]:
            print(f"   - {tenant.name} (schema: {tenant.schema_name})")

    # Recommendations
    print("\n" + "=" * 70)
    print("DIAGNOSTIC RESULTS")
    print("=" * 70)

    if not non_staff_users.exists():
        print("❌ ISSUE FOUND: No non-staff users exist!")
        print("\n📋 SOLUTION:")
        print("   Create a non-staff user using create_normal_user.py or admin interface.")
        print("   Example command:")
        print("   .\\venv\\Scripts\\python.exe create_normal_user.py")
        print("\n   Or in Django admin:")
        print("   1. Go to /admin/auth/user/add/")
        print("   2. Create user with is_staff=False")
        print("   3. Save and login as that user")
    else:
        print("✅ Non-staff users exist.")
        print("\n📋 TESTING STEPS:")
        print("   1. Login as one of the non-staff users listed above")
        print("   2. Go to the landing page")
        print("   3. Look for 'Manage My Links' button after 'Welcome Dashboard'")
        print("   4. Check browser console (F12) for any JavaScript errors")
        print("   5. Inspect the page to see if the button HTML exists but is hidden")

    print("\n" + "=" * 70)
    print("BUTTON CODE LOCATION")
    print("=" * 70)
    print("File: dose/templates/dose/landing_page.html")
    print("Lines: 908-918 (approximately)")
    print("Condition: {% if user.is_authenticated and not user.is_staff %}")
    print("=" * 70)

if __name__ == "__main__":
    test_button_visibility()
