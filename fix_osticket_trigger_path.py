import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

# Find OSTicket endpoint
osticket = PassThroughEndpoint.objects.filter(menu_title='OsTicket').first()

if osticket:
    print(f"Found OSTicket endpoint:")
    print(f"  Current trigger_path: {osticket.trigger_path}")
    print(f"  Menu title: {osticket.menu_title}")
    
    # Fix the trigger_path - use full path format
    osticket.trigger_path = '/admin/osticket/'
    osticket.save()
    
    print(f"  Updated trigger_path: {osticket.trigger_path}")
    print("✓ OSTicket trigger path updated successfully!")
else:
    print("OSTicket endpoint not found in database")
