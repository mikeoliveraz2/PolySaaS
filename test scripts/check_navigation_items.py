#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import NavigationItem, NavigationPanel
from django.db import connection

print("Checking NavigationItems for v0...")
with connection.cursor() as c:
    c.execute('SET LOCAL search_path TO olient,public;')
    items = NavigationItem.objects.filter(is_active=True)
    print(f'Found {items.count()} active NavigationItems:')
    for item in items:
        print(f'  "{item.title}": {item.url}')

    v0_items = NavigationItem.objects.filter(title__icontains='v0', is_active=True)
    if v0_items.exists():
        print(f'\n✅ Found {v0_items.count()} v0 NavigationItem(s):')
        for item in v0_items:
            print(f'  "{item.title}": {item.url} (Panel: {item.panel.title if item.panel else "None"})')
    else:
        print('\n❌ No v0 NavigationItems found')
