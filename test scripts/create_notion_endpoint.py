#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create Notion PassThroughEndpoint in Django
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint, Tenant

print("\n" + "="*100)
print("CREATING NOTION PASSTHROUGH ENDPOINT")
print("="*100 + "\n")

# Get the first tenant (usually 'public' or 'default')
tenant = Tenant.objects.first()
if not tenant:
    print("❌ No Tenant found. Create one first.")
    exit(1)

print(f"Using Tenant: {tenant.name} (schema: {tenant.schema_name})\n")

# Check if already exists
existing = PassThroughEndpoint.objects.filter(
    trigger_path__icontains='notion',
    tenant=tenant
).first()

if existing:
    print(f"✓ Notion endpoint already exists:")
    print(f"  ID: {existing.id}")
    print(f"  Trigger Path: {existing.trigger_path}")
    print(f"  Endpoint URL: {existing.endpoint_url}")
    print(f"  Is Enabled: {existing.is_enabled}")
    print()
    exit(0)

# Create new endpoint
endpoint = PassThroughEndpoint.objects.create(
    tenant=tenant,
    trigger_path='/admin/notion/',
    endpoint_url='https://www.notion.so/',
    passthrough_type='scraper',
    provider='custom',
    is_enabled=True,
    bypass_middleware=False,
    show_in_menu=True,
    description='Notion SaaS CRM for PolySaaS demo',
)

print(f"✓ Created new Notion endpoint:")
print(f"  ID: {endpoint.id}")
print(f"  Trigger Path: {endpoint.trigger_path}")
print(f"  Endpoint URL: {endpoint.endpoint_url}")
print(f"  Passthrough Type: {endpoint.passthrough_type}")
print(f"  Is Enabled: {endpoint.is_enabled}")
print(f"  Show in Menu: {endpoint.show_in_menu}")
print()
print("="*100)
print("NEXT STEPS:")
print("="*100)
print("""
1. Go to: http://localhost:8000/admin/
2. Navigate to: Passthrough Endpoints
3. Click on your new Notion endpoint
4. Verify settings and save

5. Then try accessing: http://localhost:8000/admin/notion/
6. You should see Notion sidebar loading (may take a moment)

If still stuck on spinner:
   - Check browser console (F12 > Console)
   - Make sure your Notion integration is connected to your database
   - Try hard refresh: Ctrl+Shift+R
""")
print("="*100 + "\n")
