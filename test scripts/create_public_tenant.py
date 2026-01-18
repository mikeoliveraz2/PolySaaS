#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import Tenant

public_tenant, created = Tenant.objects.get_or_create(
    schema_name='public',
    defaults={
        'name': 'Public',
        'slug': 'public',
        'description': 'Default public tenant for superusers and global access.',
        'is_active': True,
        'admin_theme': 'tech_blue',
    }
)

if created:
    print('✅ Public tenant created.')
else:
    print('ℹ️ Public tenant already exists.')
