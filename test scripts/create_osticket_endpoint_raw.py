#!/usr/bin/env python3
"""Create OSTicket PassThroughEndpoint via raw SQL"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import connection

# Delete any existing OSTicket endpoints
with connection.cursor() as cursor:
    cursor.execute("DELETE FROM dose_passthroughendpoint WHERE trigger_path = 'osticket'")
    print("✓ Cleaned up existing OSTicket endpoints")

# Insert new endpoint via raw SQL
with connection.cursor() as cursor:
    cursor.execute("""
        INSERT INTO dose_passthroughendpoint (
            is_enabled, bypass_middleware, passthrough_type, provider, endpoint_url,
            description, created_at, trigger_path, discovered_subpaths, show_in_menu,
            menu_title, menu_icon, menu_sort_order, integration_mode, api_endpoint,
            api_auth_type, api_key, api_key_header, auth_username, auth_password,
            inject_proxy_script, polysniffer_debug_output
        ) VALUES (
            true, false, 'scraper', 'custom', 'https://oliverenterprises.app.saasify.cloud/scp/',
            'OSTicket Support System', now(), 'osticket', '{}', true,
            'OSTicket Support', 'fas fa-ticket-alt', 100, 'web_only', '',
            'bearer', '', 'Authorization', '', '',
            false, '{}'
        )
    """)
    print("✓ Created OSTicket PassThroughEndpoint")

# Verify
from dose.models import PassThroughEndpoint
endpoints = PassThroughEndpoint.objects.filter(is_enabled=True)
print(f"\n📋 All enabled endpoints ({endpoints.count()}):")
for ep in endpoints:
    print(f"   trigger_path: {ep.trigger_path} → {ep.endpoint_url}")
