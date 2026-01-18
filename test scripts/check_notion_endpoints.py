#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check Notion PassThroughEndpoint configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("="*100)
print("NOTION PASSTHROUGH ENDPOINTS")
print("="*100)

endpoints = PassThroughEndpoint.objects.filter(trigger_path__icontains='notion')

if not endpoints.exists():
    print("\n❌ NO NOTION ENDPOINTS FOUND!\n")
    print("Creating diagnostic info about ALL endpoints...\n")

    all_endpoints = PassThroughEndpoint.objects.all()
    print(f"Total PassThroughEndpoint records: {all_endpoints.count()}\n")

    for ep in all_endpoints[:10]:
        print(f"  ID: {ep.id}")
        print(f"  Trigger Path: {ep.trigger_path}")
        print(f"  Endpoint URL: {ep.endpoint_url}")
        print(f"  Is Enabled: {ep.is_enabled}")
        print(f"  Bypass Middleware: {getattr(ep, 'bypass_middleware', False)}")
        print()
else:
    print(f"\n✓ Found {endpoints.count()} Notion endpoint(s)\n")

    for ep in endpoints:
        print(f"ID: {ep.id}")
        print(f"Trigger Path: {ep.trigger_path}")
        print(f"Endpoint URL: {ep.endpoint_url}")
        print(f"Is Enabled: {ep.is_enabled}")
        print(f"Bypass Middleware: {getattr(ep, 'bypass_middleware', False)}")
        print()

print("="*100)
