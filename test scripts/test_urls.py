#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose import urls

print(f"\n=== DOSE URL PATTERNS ===")
print(f"Total patterns: {len(urls.urlpatterns)}\n")

for i, pattern in enumerate(urls.urlpatterns):
    name = getattr(pattern, 'name', 'NO_NAME')
    pattern_str = str(getattr(pattern, 'pattern', pattern))
    print(f"{i+1:3d}. {name:30s} {pattern_str}")

print("\n=== NAVIGATION PATTERNS ===")
nav_patterns = [p for p in urls.urlpatterns if hasattr(p, 'name') and p.name and 'nav' in p.name.lower()]
if nav_patterns:
    for p in nav_patterns:
        print(f"  - {p.name}: {p.pattern}")
else:
    print("  NONE FOUND!")

print("\n=== CHECKING IMPORTS ===")
print(f"api_get_nav_modal in dir(urls): {'api_get_nav_modal' in dir(urls)}")
try:
    print(f"urls.api_get_nav_modal: {urls.api_get_nav_modal}")
except AttributeError as e:
    print(f"ERROR: {e}")
