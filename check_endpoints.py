#!/usr/bin/env python
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint

eps = PassThroughEndpoint.objects.all()
print(f'Total PassThroughEndpoints: {eps.count()}')
for ep in eps:
    print(f'  - {ep.endpoint_url}')
