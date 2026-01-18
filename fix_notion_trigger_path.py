#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix Notion trigger path and diagnose passthrough issue
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint, Tenant

print("\n" + "="*100)
print("FIXING NOTION TRIGGER PATH")
print("="*100 + "\n")

# Find Notion endpoint
endpoint = PassThroughEndpoint.objects.filter(
    trigger_path__icontains='tion'
).first()

if not endpoint:
    print("❌ No Notion endpoint found")
    exit(1)

print(f"Found endpoint:")
print(f"  Current Trigger Path: '{endpoint.trigger_path}'")
print(f"  Endpoint URL: {endpoint.endpoint_url}")
print()

# Fix the trigger path
old_path = endpoint.trigger_path
endpoint.trigger_path = '/notion/'
endpoint.save()

print(f"✓ Updated Trigger Path:")
print(f"  Old: '{old_path}'")
print(f"  New: '{endpoint.trigger_path}'")
print()

print("="*100)
print("NEXT STEPS:")
print("="*100)
print("""
1. Go to: http://localhost:8000/notion/
   (This will trigger the passthrough middleware)

2. You should see Notion sidebar loading

3. If still stuck on spinner:
   - Open browser console: F12 > Console
   - Look for errors (usually CORS or auth issues)
   - Try hard refresh: Ctrl+Shift+R

4. Common Notion loading issues:
   - Integration not connected to database
   - Wrong database ID in your Python config
   - Browser security blocking iframe content

5. To bypass UI issues, test with API:
   Run: python test_notion_api.py
""")
print("="*100 + "\n")
