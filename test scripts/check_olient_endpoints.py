#!/usr/bin/env python3
import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import connection
from dose.models import PassThroughEndpoint

# Switch to olient schema
with connection.cursor() as cursor:
    cursor.execute("SET search_path TO olient,public;")

# Check what OSTicket endpoints exist
endpoints = PassThroughEndpoint.objects.filter(trigger_path__icontains='osticket')
print(f"\n📋 OSTicket endpoints in olient schema: {endpoints.count()}")
for ep in endpoints:
    print(f"\n   ID: {ep.id}")
    print(f"   trigger_path: '{ep.trigger_path}'")
    print(f"   endpoint_url: {ep.endpoint_url}")
    print(f"   passthrough_type: {ep.passthrough_type}")
    print(f"   is_enabled: {ep.is_enabled}")

# Also check all endpoints
all_eps = PassThroughEndpoint.objects.filter(is_enabled=True)
print(f"\n📋 All enabled endpoints in olient schema: {all_eps.count()}")
for ep in all_eps:
    print(f"   trigger_path='{ep.trigger_path}' → {ep.endpoint_url}")
