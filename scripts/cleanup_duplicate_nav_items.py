#!/usr/bin/env python
"""
Delete NavigationItem records that duplicate PassThroughEndpoint entries.
PassThroughEndpoint is the authoritative source for passthrough services.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

import django
django.setup()

from django.db import connection
from dose.models import PassThroughEndpoint, NavigationItem

def main():
    # Set schema to olient
    with connection.cursor() as cur:
        cur.execute('SET search_path TO olient,public;')

    # Get all PassThroughEndpoint triggers (normalized)
    pt_triggers = set()
    pt_urls = set()
    for ep in PassThroughEndpoint.objects.filter(is_enabled=True):
        norm = ep.trigger_path.strip('/').lower().split('/')[-1].replace('-', '_')
        pt_triggers.add(norm)
        pt_urls.add(ep.endpoint_url.rstrip('/').lower())
        print(f'PassThroughEndpoint: {ep.trigger_path} -> normalized: {norm}, url: {ep.endpoint_url}')

    print()
    print('=== NavigationItems to DELETE (duplicates of PassThroughEndpoints) ===')

    # Find NavigationItems that duplicate PassThroughEndpoints
    to_delete = []
    for item in NavigationItem.objects.all():
        title_norm = item.title.lower().replace(' ', '_').replace('-', '_')
        url_norm = item.url.rstrip('/').lower()
        
        # Check if URL matches a passthrough endpoint URL
        if url_norm in pt_urls:
            print(f'  DELETE: NavigationItem ID={item.id} title="{item.title}" url={item.url} (URL matches PT endpoint)')
            to_delete.append(item.id)
            continue
            
        # Check if title matches a passthrough trigger
        for trigger in pt_triggers:
            if trigger in title_norm or title_norm in trigger:
                print(f'  DELETE: NavigationItem ID={item.id} title="{item.title}" url={item.url} (title matches PT trigger "{trigger}")')
                to_delete.append(item.id)
                break

    print()
    if to_delete:
        print(f'Deleting {len(to_delete)} duplicate NavigationItems...')
        deleted = NavigationItem.objects.filter(id__in=to_delete).delete()
        print(f'Deleted: {deleted}')
    else:
        print('No duplicates found.')

if __name__ == '__main__':
    main()
