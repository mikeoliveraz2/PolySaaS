import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint, NavigationItem

print("=== Checking for duplicate Gmail entries ===\n")

# Check PassThroughEndpoint
gmail_passthrough = PassThroughEndpoint.objects.filter(trigger_path__icontains='gmail')
print(f"PassThroughEndpoint Gmail entries: {gmail_passthrough.count()}")
for entry in gmail_passthrough:
    print(f"  ID={entry.id}, path={entry.trigger_path}, title={entry.menu_title}, show_in_menu={entry.show_in_menu}")

print()

# Check NavigationItem
gmail_nav_items = NavigationItem.objects.filter(title__icontains='gmail')
print(f"NavigationItem Gmail entries: {gmail_nav_items.count()}")
for item in gmail_nav_items:
    print(f"  ID={item.id}, title={item.title}, url={item.url}")

print("\n=== Solution ===")
total_gmail = gmail_passthrough.count() + gmail_nav_items.count()
if total_gmail > 1:
    print(f"DUPLICATES FOUND: {total_gmail} Gmail entries total")
    if gmail_passthrough.count() > 1:
        print(f"  - {gmail_passthrough.count()} PassThroughEndpoint entries (should be 1)")
    if gmail_nav_items.count() > 0:
        print(f"  - {gmail_nav_items.count()} NavigationItem entries (should be 0)")
    print("\nRecommendation:")
    print("  1. Keep ONE PassThroughEndpoint for Gmail (/dose/gmail/ preferred)")
    print("  2. Delete any NavigationItem Gmail entries")
    print("  3. Delete duplicate PassThroughEndpoint entries")
