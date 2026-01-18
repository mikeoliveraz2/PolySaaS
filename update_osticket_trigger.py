#!/usr/bin/env python
"""
Update OSTicket trigger_path to simple name
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.db import connection
from dose.models.pass_through_endpoint import PassThroughEndpoint

# Set schema to olient
with connection.cursor() as cursor:
    cursor.execute("SET search_path TO olient,public;")

print("Updating OSTicket trigger_path...")

try:
    ep = PassThroughEndpoint.objects.get(trigger_path='/admin/osticket/')
    ep.trigger_path = 'osticket'
    ep.save()
    print("Updated OSTicket trigger_path to 'osticket'")
except PassThroughEndpoint.DoesNotExist:
    print("OSTicket endpoint with '/admin/osticket/' not found")

print("Done!")