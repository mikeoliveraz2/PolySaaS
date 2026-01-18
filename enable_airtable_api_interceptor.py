#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enable API interceptor script for Airtable endpoint
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

print("\nEnabling API interceptor for Airtable...\n")

endpoints = PassThroughEndpoint.objects.filter(trigger_path__icontains='airtable')

for ep in endpoints:
    print(f"Endpoint: {ep.trigger_path}")
    ep.inject_proxy_script = True
    ep.save()
    print(f"✓ API interceptor enabled")

print("\n✓ Done! Airtable will now have the API interceptor script injected.\n")
