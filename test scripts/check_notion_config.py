#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check current Notion endpoint configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

endpoints = PassThroughEndpoint.objects.filter(trigger_path__icontains='notion')

print("\nCurrent Notion Endpoint Configuration:")
print("="*100)

if endpoints.exists():
    for ep in endpoints:
        print(f"Trigger Path: {ep.trigger_path}")
        print(f"Endpoint URL: {ep.endpoint_url}")
        print(f"Description: {ep.description}")
        print()
else:
    print("No Notion endpoint found")

print("="*100)
