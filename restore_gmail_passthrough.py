#!/usr/bin/env python3
"""
Restore Gmail PassThroughEndpoint record
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from dose.models import PassThroughEndpoint

def restore_gmail_passthrough():
    """Restore the Gmail passthrough record"""

    # Check if Gmail passthrough already exists
    existing = PassThroughEndpoint.objects.filter(trigger_path__icontains='gmail')
    if existing.exists():
        print(f"Found {existing.count()} existing Gmail passthrough records:")
        for record in existing:
            print(f"  ID: {record.id}, Path: {record.trigger_path}, Enabled: {record.is_enabled}")
        return

    # Create the Gmail passthrough record
    gmail_endpoint = PassThroughEndpoint.objects.create(
        trigger_path='/dose/gmail/',
        endpoint_url='https://mail.google.com/mail/u/0/?tab=rm&ogbl',
        menu_title='Gmail',
        description='Gmail',
        is_enabled=True,
        show_in_menu=True
    )

    print(f"✅ Created Gmail passthrough record:")
    print(f"   ID: {gmail_endpoint.id}")
    print(f"   Trigger path: {gmail_endpoint.trigger_path}")
    print(f"   Menu title: {gmail_endpoint.menu_title}")
    print(f"   Show in menu: {gmail_endpoint.show_in_menu}")
    print(f"   Enabled: {gmail_endpoint.is_enabled}")

if __name__ == "__main__":
    restore_gmail_passthrough()