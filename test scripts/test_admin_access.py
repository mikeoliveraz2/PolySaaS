#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import Client
# from dose.models import TenantUser  # Model not found, update if exists elsewhere

# Create a test client
client = Client()

# Login
login_response = client.login(username='admin', password='admin123')
print(f"Login successful: {login_response}")

if login_response:
    # Test access to tenant admin
    response = client.get('/admin/dose/tenant/')
    print(f"Tenant admin status: {response.status_code}")
    print(f"Response type: {response.get('Content-Type', 'unknown')}")
    
    if response.status_code == 200:
        print("✅ Tenant admin page is accessible!")
    else:
        print(f"❌ Issue with tenant admin page: {response.status_code}")
        print("Response content preview:")
        print(response.content.decode('utf-8')[:500])
else:
    print("❌ Login failed - check credentials")
