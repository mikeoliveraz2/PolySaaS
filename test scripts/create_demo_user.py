#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from dose.models import Tenant, UserProfile

def show_tenants_and_create_user():
    print("=== Available Tenants ===")
    tenants = Tenant.objects.all()
    for tenant in tenants:
        print(f"ID: {tenant.id} | Name: {tenant.name} | Slug: {tenant.slug}")
    
    if not tenants.exists():
        print("No tenants found! Creating a demo tenant first...")
        demo_tenant = Tenant.objects.create(
            name="Demo Organization",
            slug="demo",
            description="Demo tenant for testing",
            tagline="This is a demo organization"
        )
        print(f"Created demo tenant: ID {demo_tenant.id}")
    else:
        # Use the first available tenant
        demo_tenant = tenants.first()
        print(f"Using tenant: {demo_tenant.name} (ID: {demo_tenant.id})")
    
    # Check if demouser already exists
    if User.objects.filter(username='demouser').exists():
        print("demouser already exists!")
        user = User.objects.get(username='demouser')
    else:
        print("Creating demouser...")
        user = User.objects.create_user(
            username='demouser',
            email='demo@example.com',
            password='demo123',
            first_name='Demo',
            last_name='User'
        )
        print("demouser created successfully!")
    
    # Check if UserProfile exists
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'tenant': demo_tenant}
    )
    
    if created:
        print(f"Created UserProfile linking demouser to {demo_tenant.name}")
    else:
        print(f"UserProfile already exists: demouser -> {profile.tenant.name}")
    
    print("\n=== Login Credentials ===")
    print("Username: demouser")
    print("Password: demo123")
    print(f"Tenant: {profile.tenant.name}")

if __name__ == "__main__":
    show_tenants_and_create_user()
