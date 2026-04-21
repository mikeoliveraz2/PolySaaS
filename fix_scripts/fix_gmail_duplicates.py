import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint, NavigationItem

print("=== Removing Gmail Duplicates ===\n")

# Delete NavigationItem Gmail entry
nav_item = NavigationItem.objects.filter(id=51).first()
if nav_item:
    print(f"Deleting NavigationItem: {nav_item.title} ({nav_item.url})")
    nav_item.delete()
    print("✓ Deleted")
else:
    print("NavigationItem not found")

print()

# Delete the /admin/gmail/ PassThroughEndpoint (keep /dose/gmail/)
admin_gmail = PassThroughEndpoint.objects.filter(id=1, trigger_path='/admin/gmail/').first()
if admin_gmail:
    print(f"Deleting PassThroughEndpoint: {admin_gmail.menu_title} ({admin_gmail.trigger_path})")
    admin_gmail.delete()
    print("✓ Deleted")
else:
    print("Admin Gmail PassThroughEndpoint not found")

print()

# Verify only one Gmail entry remains
remaining_gmail = PassThroughEndpoint.objects.filter(trigger_path__icontains='gmail')
print(f"Remaining Gmail PassThroughEndpoint entries: {remaining_gmail.count()}")
for entry in remaining_gmail:
    print(f"  ✓ ID={entry.id}, path={entry.trigger_path}, title={entry.menu_title}")

print("\n=== Done ===")
