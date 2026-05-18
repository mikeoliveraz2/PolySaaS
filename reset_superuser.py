#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# Reset superuser password
superuser = User.objects.get(username='superuser')
superuser.set_password('admin123')
superuser.save()
print(f"✓ Superuser password reset to: admin123")
print(f"  Username: superuser")
