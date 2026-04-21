#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix Airtable endpoint trigger path to match PolySaaS /pt/admin/ pattern
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("\nFixing Airtable endpoint trigger path...\n")

endpoints = PassThroughEndpoint.objects.filter(trigger_path__icontains='airtable')

for ep in endpoints:
    print(f"Current endpoint:")
    print(f"  Trigger Path: {ep.trigger_path}")
    print(f"  Endpoint URL: {ep.endpoint_url}")

    old_path = ep.trigger_path
    ep.trigger_path = '/pt/admin/airtable/'
    ep.endpoint_url = 'https://airtable.com/'
    ep.save()

    print(f"\n✓ Updated:")
    print(f"  Trigger Path: {old_path} → {ep.trigger_path}")
    print(f"  Endpoint URL: {ep.endpoint_url}")
    print(f"\nNow visit: http://127.0.0.1:8000/pt/admin/airtable/")
