#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib import admin
from django.test import RequestFactory
from django.contrib.auth.models import User

# Create a mock request with a superuser
factory = RequestFactory()
request = factory.get('/admin/')
superuser = User.objects.filter(is_superuser=True).first()
if superuser:
    request.user = superuser
    apps = admin.site.get_app_list(request)
    print(f'\nTotal apps registered: {len(apps)}\n')
    for app in apps:
        print(f"{app['name']}: {len(app.get('models', []))} models")
        for model in app.get('models', []):
            print(f"  - {model['name']}")
else:
    print("No superuser found")
    # Just list all registered models
    print(f'\nAll registered models in admin.site:')
    for model, admin_class in admin.site._registry.items():
        print(f"  - {model.__name__}")
