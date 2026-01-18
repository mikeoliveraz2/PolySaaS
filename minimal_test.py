#!/usr/bin/env python
import os
import sys

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

print("\n=== IMPORTING dose.urls ===\n")

# This should trigger all the print statements in dose/urls.py
import dose.urls

print("\n=== IMPORT COMPLETE ===\n")
print(f"Total URL patterns: {len(dose.urls.urlpatterns)}")
print(f"\nFirst 5 patterns:")
for i, p in enumerate(dose.urls.urlpatterns[:5]):
    print(f"  {i+1}. {getattr(p, 'name', 'NO_NAME')}")

print(f"\nLast 5 patterns:")
for i, p in enumerate(dose.urls.urlpatterns[-5:]):
    print(f"  {len(dose.urls.urlpatterns)-4+i}. {getattr(p, 'name', 'NO_NAME')}")
