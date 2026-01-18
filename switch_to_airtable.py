#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Switch PassThroughEndpoint from Notion to Airtable
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("\n" + "="*100)
print("SWITCHING PASSTHROUGH TO AIRTABLE")
print("="*100 + "\n")

# Find existing endpoint (Notion or any)
endpoint = PassThroughEndpoint.objects.filter(
    trigger_path__icontains='notion'
).first()

if not endpoint:
    # Try to find any passthrough and update it
    endpoint = PassThroughEndpoint.objects.filter(
        trigger_path__contains='/'
    ).first()

if not endpoint:
    print("❌ No existing endpoint found. Creating new one...")
    endpoint = PassThroughEndpoint.objects.create(
        trigger_path='/airtable/',
        endpoint_url='https://airtable.com/',
        passthrough_type='scraper',
        provider='custom',
        is_enabled=True,
        bypass_middleware=False,
        show_in_menu=True,
        description='Airtable CRM for PolySaaS demo',
    )
else:
    # Update existing
    endpoint.trigger_path = '/airtable/'
    endpoint.endpoint_url = 'https://airtable.com/'
    endpoint.description = 'Airtable CRM for PolySaaS demo'
    endpoint.save()

print(f"✓ Passthrough Endpoint Updated:")
print(f"  Trigger Path: {endpoint.trigger_path}")
print(f"  Endpoint URL: {endpoint.endpoint_url}")
print(f"  Is Enabled: {endpoint.is_enabled}")
print()

print("="*100)
print("NEXT STEPS:")
print("="*100)
print("""
1. In Airtable:
   - Create a new base (or use existing)
   - Create a table called "Contacts" with fields:
     * Name (text)
     * Email (email)
     * Phone (phone number)
     * Company (text)
     * Status (single select)

2. Get your Airtable credentials:
   - Go to: https://airtable.com/account/tokens
   - Create a "Personal access token"
   - Copy the token (starts with pat_...)

3. Get your Base ID:
   - In Airtable, open your base
   - URL shows: airtable.com/app/[BASE_ID]/...
   - Copy that ID

4. Test via API first:
   Run: python test_airtable_api.py

5. Then try passthrough:
   Visit: http://localhost:8000/airtable/
""")
print("="*100 + "\n")
