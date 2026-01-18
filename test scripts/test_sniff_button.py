"""
Test script to verify Sniff button is working
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib import admin
from dose.models import PassThroughEndpoint
from dose.admin import PassThroughEndpointAdmin

print("=" * 60)
print("CHECKING SNIFF BUTTON CONFIGURATION")
print("=" * 60)

# 1. Check if admin is registered
admin_class = admin.site._registry.get(PassThroughEndpoint)
if admin_class:
    print("[OK] PassThroughEndpoint is registered with admin")
    print(f"   Admin class: {admin_class.__class__.__name__}")
else:
    print("[ERROR] PassThroughEndpoint is NOT registered!")
    exit(1)

# 2. Check list_display
print(f"\n[OK] list_display: {admin_class.list_display}")
if 'debug_button' in admin_class.list_display:
    print("   [OK] 'debug_button' is in list_display")
else:
    print("   [ERROR] 'debug_button' is NOT in list_display!")
    exit(1)

# 3. Check if method exists
if hasattr(admin_class, 'debug_button'):
    print("   [OK] 'debug_button' method exists")
else:
    print("   [ERROR] 'debug_button' method does NOT exist!")
    exit(1)

# 4. Test the method with a real endpoint
ep = PassThroughEndpoint.objects.filter(endpoint_url__isnull=False).first()
if ep:
    print(f"\n[OK] Testing with endpoint: {ep.get_menu_title()}")
    print(f"   Endpoint URL: {ep.endpoint_url}")
    admin_instance = PassThroughEndpointAdmin(PassThroughEndpoint, None)
    result = admin_instance.debug_button(ep)
    if result:
        print(f"   [OK] Button method returns HTML (length: {len(str(result))})")
        print(f"   First 150 chars: {str(result)[:150]}")
    else:
        print("   [ERROR] Button method returns None or empty!")
else:
    print("\n[WARNING] No endpoints with URLs found to test")

# 5. Check short_description
if hasattr(admin_class.debug_button, 'short_description'):
    desc = admin_class.debug_button.short_description
    print(f"\n[OK] Column header set (contains emoji, length: {len(desc)})")
else:
    print("\n[WARNING] No short_description set")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("If all checks pass, the button SHOULD be visible.")
print("If you don't see it:")
print("1. RESTART your Django server (stop and start)")
print("2. Hard refresh browser (Ctrl+F5)")
print("3. Go to: http://localhost:8000/admin/dose/passthroughendpoint/")
print("4. Look for column header 'Sniff' between 'Is enabled' and 'Created at'")
print("=" * 60)
