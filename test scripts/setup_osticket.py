#!/usr/bin/env python3
"""Create OSTicket PassThroughEndpoint - minimal approach"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import connection

# Clean up
with connection.cursor() as cursor:
    cursor.execute("DELETE FROM dose_passthroughendpoint WHERE trigger_path LIKE '%osticket%'")

# Create endpoint with all required fields
sql = """
INSERT INTO dose_passthroughendpoint (
    is_enabled, bypass_middleware, passthrough_type, provider, endpoint_url,
    description, created_at, trigger_path, discovered_subpaths, show_in_menu,
    menu_title, menu_icon, menu_sort_order, integration_mode, api_endpoint,
    api_auth_type, api_key, api_key_header, auth_username, auth_password,
    inject_proxy_script, polysniffer_debug_output, handler_class, handler_code
) VALUES (
    true, false, 'scraper', 'custom', %s,
    %s, now(), %s, %s, true,
    %s, %s, 100, 'web_only', '',
    'bearer', '', 'Authorization', '', '',
    false, '', '', ''
)
"""

with connection.cursor() as cursor:
    cursor.execute(sql, [
        'https://oliverenterprises.app.saasify.cloud/scp/',  # endpoint_url
        'OSTicket Support System',  # description
        'osticket',  # trigger_path
        '[]',  # discovered_subpaths (JSON)
        'OSTicket Support',  # menu_title
        'fas fa-ticket-alt',  # menu_icon
    ])

print("✅ Created OSTicket PassThroughEndpoint")

# Verify
from dose.models import PassThroughEndpoint
endpoints = PassThroughEndpoint.objects.filter(trigger_path__icontains='osticket')
print(f"\n📋 OSTicket endpoints ({endpoints.count()}):")
for ep in endpoints:
    print(f"   ID: {ep.id}")
    print(f"   trigger_path: {ep.trigger_path}")
    print(f"   endpoint_url: {ep.endpoint_url}")
    print(f"   passthrough_type: {ep.passthrough_type}")
    print(f"   is_enabled: {ep.is_enabled}")
