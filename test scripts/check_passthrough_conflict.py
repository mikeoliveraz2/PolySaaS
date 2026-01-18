#!/usr/bin/env python3
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from dose.models import PassThroughEndpoint

endpoints = PassThroughEndpoint.objects.filter(is_enabled=True)
print(f'Enabled PassThroughEndpoint records: {endpoints.count()}')
for e in endpoints:
    print(f'ID: {e.id}, Path: "{e.trigger_path}", URL: {e.endpoint_url}')

print('\nChecking if any path could match /dose/gmail/:')
test_path = '/dose/gmail/'
for e in endpoints:
    if e.trigger_path:
        trigger_normalized = e.trigger_path.rstrip('/') + '/'
        test_normalized = test_path.rstrip('/') + '/'
        if test_normalized.startswith(trigger_normalized.rstrip('/')):
            print(f'  POTENTIAL MATCH: "{e.trigger_path}" could match "{test_path}"')