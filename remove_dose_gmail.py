import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint, NavigationItem

print("=== Removing /dose/gmail/ duplicate ===\n")

# Delete the /dose/gmail/ PassThroughEndpoint (ID=4)
dose_gmail = PassThroughEndpoint.objects.filter(id=4, trigger_path='/dose/gmail/').first()
if dose_gmail:
    print(f"Deleting PassThroughEndpoint: {dose_gmail.menu_title} ({dose_gmail.trigger_path})")
    dose_gmail.delete()
    print("✓ Deleted /dose/gmail/")
else:
    print("/dose/gmail/ PassThroughEndpoint not found or already deleted")

print()

# Delete the NavigationItem pointing to /admin/gmail/ (ID=51) - duplicate of PassThroughEndpoint
nav_item = NavigationItem.objects.filter(id=51, url='/admin/gmail/').first()
if nav_item:
    print(f"Deleting NavigationItem: {nav_item.title} ({nav_item.url})")
    nav_item.delete()
    print("✓ Deleted NavigationItem duplicate")
else:
    print("NavigationItem not found or already deleted")

print()

# Verify only one Gmail entry remains
remaining_passthrough = PassThroughEndpoint.objects.filter(trigger_path__icontains='gmail')
remaining_navitem = NavigationItem.objects.filter(title__icontains='gmail')

print(f"Remaining PassThroughEndpoint Gmail entries: {remaining_passthrough.count()}")
for entry in remaining_passthrough:
    print(f"  ✓ ID={entry.id}, path={entry.trigger_path}, title={entry.menu_title}")

print(f"\nRemaining NavigationItem Gmail entries: {remaining_navitem.count()}")

print("\n=== Done - Kept /admin/gmail/ only ===")
