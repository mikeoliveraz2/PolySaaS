#!/usr/bin/env python3
"""
Test Gmail API endpoints directly
"""

import os
import sys
import django
import requests

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()

    from django.test import Client
    from django.contrib.auth.models import User

    # Test with Django test client
    client = Client()
    user = User.objects.first()

    if user:
        client.force_login(user)

        print("=== Testing Gmail API Endpoints ===")

        # Test the basic Gmail API endpoint
        print("\n1. Testing Gmail messages endpoint...")
        response = client.get('/dose/gmail-api/gmail/v1/users/me/messages?maxResults=5')
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            import json
            try:
                data = json.loads(response.content.decode())
                print(f"Response: {data}")
            except:
                print(f"Response (text): {response.content.decode()[:200]}...")
        else:
            print(f"Error response: {response.content.decode()[:200]}...")

        # Test a simple test endpoint
        print("\n2. Testing simple Gmail API test...")
        response = client.get('/dose/gmail-api/test')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.content.decode()[:200]}...")

    else:
        print("No users found in database")

except Exception as e:
    print(f"Error setting up Django: {e}")
    import traceback
    traceback.print_exc()