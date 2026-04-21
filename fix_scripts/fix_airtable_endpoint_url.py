#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix Airtable endpoint URL
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("\nFixing Airtable endpoint URL...\n")

endpoints = PassThroughEndpoint.objects.filter(trigger_path__icontains='airtable')

for ep in endpoints:
    print(f"Current endpoint:")
    print(f"  Trigger Path: {ep.trigger_path}")
    print(f"  Endpoint URL: {ep.endpoint_url}")

    # Fix: endpoint_url should be the base domain, not include the trigger path
    old_url = ep.endpoint_url
    ep.endpoint_url = 'https://airtable.com/'
    ep.save()

    print(f"\n✓ Updated:")
    print(f"  Old: {old_url}")
    print(f"  New: {ep.endpoint_url}")
    print(f"\nNow when you visit /airtable/, it will proxy to https://airtable.com/")
