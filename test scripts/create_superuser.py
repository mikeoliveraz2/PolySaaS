#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()


from django.contrib.auth.models import User

try:
    user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print(f'Superuser created successfully: {user.username}')
except Exception as e:
    print(f'Error creating superuser: {e}')
