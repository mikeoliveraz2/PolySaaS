"""
Check user permissions and make user staff
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User

print("\n" + "="*70)
print("CHECKING USER PERMISSIONS")
print("="*70)

# Find the user
try:
    user = User.objects.get(username='michael')
    print(f"\nUser: {user.username}")
    print(f"Email: {user.email}")
    print(f"is_staff: {user.is_staff}")
    print(f"is_superuser: {user.is_superuser}")
    print(f"is_active: {user.is_active}")

    if not user.is_staff:
        print("\n⚠️  USER IS NOT STAFF - This is why they're redirected to login!")
        print("\nMaking user staff...")
        user.is_staff = True
        user.save()
        print("✅ User is now staff and can access /admin/")
    else:
        print("\n✅ User is already staff")

except User.DoesNotExist:
    print("\n❌ User 'michael' not found")
    print("\nLet's check all users:")
    for u in User.objects.all():
        print(f"  - {u.username}: staff={u.is_staff}, superuser={u.is_superuser}")
