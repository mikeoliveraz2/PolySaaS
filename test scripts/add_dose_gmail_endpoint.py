"""
Add /dose/gmail/ endpoint for regular users (non-staff)
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

def add_dose_gmail_endpoint():
    """Add /dose/gmail/ endpoint if it doesn't exist"""

    # Check if it exists
    existing = PassThroughEndpoint.objects.filter(trigger_path='/dose/gmail/').first()

    if existing:
        print(f"✅ /dose/gmail/ endpoint already exists")
        print(f"   type={existing.passthrough_type}, bypass={existing.bypass_middleware}, enabled={existing.is_enabled}")
        return

    # Use raw SQL to insert with discovered_subpaths (DB field not in model)
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO dose_passthroughendpoint
            (is_enabled, bypass_middleware, passthrough_type, provider, endpoint_url, description,
             trigger_path, show_in_menu, menu_title, menu_icon, menu_sort_order, created_at, discovered_subpaths)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """, [
            True,  # is_enabled
            True,  # bypass_middleware
            'api',  # passthrough_type
            'google',  # provider
            'https://www.googleapis.com/gmail/v1/users/me',  # endpoint_url
            'Gmail API for regular users (non-staff)',  # description
            '/dose/gmail/',  # trigger_path
            True,  # show_in_menu
            'Gmail',  # menu_title
            'fa fa-envelope',  # menu_icon
            10,  # menu_sort_order
            []  # discovered_subpaths (empty array)
        ])

    print(f"✅ Created /dose/gmail/ endpoint")

    # List all endpoints
    print("\n📋 All PassThroughEndpoint records:")
    for ep in PassThroughEndpoint.objects.all():
        print(f"  - {ep.trigger_path}: type={ep.passthrough_type}, bypass={ep.bypass_middleware}, enabled={ep.is_enabled}")

if __name__ == '__main__':
    add_dose_gmail_endpoint()
