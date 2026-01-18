#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
from django.test import RequestFactory
from django.contrib.auth.models import User
from dose.context_processors import admin_navigation

# Get or create a test request
factory = RequestFactory()
request = factory.get('/admin/')

# Add a user to the request
user = User.objects.first()
if user:
    request.user = user
    print(f"✅ Testing with user: {user.username}\n")
else:
    print("❌ No users found in database\n")
    exit(1)

# Check endpoints in DB
print("📊 PassThroughEndpoint records in DB:")
endpoints = PassThroughEndpoint.objects.all()
for ep in endpoints:
    print(f"  ID={ep.id}: {ep.menu_title} (enabled={ep.is_enabled}, show_in_menu={ep.show_in_menu})")

print(f"\nTotal: {endpoints.count()}")

# Filter by is_enabled and show_in_menu
filtered = PassThroughEndpoint.objects.filter(is_enabled=True, show_in_menu=True)
print(f"\n✅ Filtered (is_enabled=True, show_in_menu=True): {filtered.count()}")
for ep in filtered:
    print(f"  ID={ep.id}: {ep.menu_title}")

# Call the context processor
print("\n🔍 Calling admin_navigation context processor...\n")
context = admin_navigation(request)

print(f"✅ Context keys: {context.keys()}")
print(f"✅ Passthrough services count: {len(context.get('passthrough_services', []))}")

for i, svc in enumerate(context.get('passthrough_services', []), 1):
    print(f"\n  Service {i}:")
    print(f"    Title: {svc.get('title')}")
    print(f"    URL: {svc.get('url')}")
    print(f"    Icon: {svc.get('icon')}")
