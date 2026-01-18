#!/usr/bin/env python
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

# Test if we can execute the urlpatterns construction step by step
print("\n=== TESTING URL PATTERN CONSTRUCTION ===\n")

from dose.views.main import (
    api_get_nav_modal, api_get_nav_panels, api_get_my_nav_items,
    api_create_nav_item, api_delete_nav_item, api_update_nav_item
)
from django.urls import path

print(f"✓ Imported navigation functions successfully")
print(f"  api_get_nav_modal: {api_get_nav_modal}")

# Try to construct the path objects individually
try:
    p1 = path('api/nav-modal/', api_get_nav_modal, name='api_nav_modal')
    print(f"✓ Created path for api_nav_modal: {p1}")
except Exception as e:
    print(f"✗ Failed to create path for api_nav_modal: {e}")
    sys.exit(1)

try:
    p2 = path('api/nav-panels/', api_get_nav_panels, name='api_nav_panels')
    print(f"✓ Created path for api_nav_panels: {p2}")
except Exception as e:
    print(f"✗ Failed to create path for api_nav_panels: {e}")
    sys.exit(1)

# Now test if they work in a list
try:
    test_patterns = [
        path('api/nav-modal/', api_get_nav_modal, name='api_nav_modal'),
        path('api/nav-panels/', api_get_nav_panels, name='api_nav_panels'),
    ]
    print(f"\n✓ Successfully created list with {len(test_patterns)} navigation patterns")
except Exception as e:
    print(f"\n✗ Failed to create pattern list: {e}")
    sys.exit(1)

print("\n=== ALL TESTS PASSED ===\n")
