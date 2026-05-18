#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

print("Users in database:")
for u in User.objects.all()[:15]:
    print(f"  {u.username:30} | email={u.email:30} | active={u.is_active}")

print(f"\nTotal users: {User.objects.count()}")
