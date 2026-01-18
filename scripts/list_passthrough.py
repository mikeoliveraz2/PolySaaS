#!/usr/bin/env python3
"""Query enabled PassThroughEndpoint records and print ID, trigger_path and endpoint_url.

Run from the repo root inside the project's venv:
  .venv\Scripts\python scripts\list_passthrough.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

try:
    import django
    django.setup()
except Exception as e:
    print('Django setup failed:', e)
    raise

from dose.models import PassThroughEndpoint

qs = PassThroughEndpoint.objects.filter(is_enabled=True)
print('COUNT:', qs.count())
for p in qs:
    print('ID:%s path:%s url:%s' % (p.id, p.trigger_path, p.endpoint_url))
