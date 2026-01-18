#!/usr/bin/env python
"""
Check user permissions and what page they should see
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User

print("=" * 60)
print("USER PERMISSIONS CHECK")
print("=" * 60)

try:
    user = User.objects.get(username='michael')
    print(f"\n✅ User: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   is_staff: {user.is_staff}")
    print(f"   is_superuser: {user.is_superuser}")
    print(f"   is_active: {user.is_active}")

    print("\n" + "=" * 60)
    print("EXPECTED PAGE ROUTING:")
    print("=" * 60)

    if user.is_staff or user.is_superuser:
        print("✅ User IS staff/superuser")
        print("   → Should redirect to: /admin/ (Jazzmin admin interface)")
        print("   → Will see landing_page.html with ADMIN INTERFACE link")
    else:
        print("✅ User is regular user (not staff)")
        print("   → Should redirect to: /user-dashboard/ (AdminLTE interface)")
        print("   → Will see user_dashboard.html")

    print("\n" + "=" * 60)
    print("TO TEST USER DASHBOARD:")
    print("=" * 60)
    print("Option 1: Create a new non-staff user")
    print("Option 2: Temporarily set michael.is_staff = False")
    print("\nWould you like me to:")
    print("  A) Create a demo non-staff user?")
    print("  B) Keep michael as staff and create 'testuser' as non-staff?")

except User.DoesNotExist:
    print("❌ User 'michael' not found")
