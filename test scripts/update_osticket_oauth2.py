#!/usr/bin/env python
"""
Update OSTicket PassThroughEndpoint to use Google OAuth2 authentication
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
from django.contrib.auth.models import User

print("="*60)
print("Updating OSTicket to use Google OAuth2")
print("="*60)
print()

# Find OSTicket endpoint
osticket = PassThroughEndpoint.objects.filter(
    trigger_path__icontains='osticket'
).first()

if not osticket:
    print("ERROR: OSTicket endpoint not found!")
    exit(1)

print(f"Found OSTicket endpoint ID: {osticket.id}")
print(f"  Current Provider: {osticket.provider}")
print(f"  Current API Auth Type: {osticket.api_auth_type}")
print(f"  Current Endpoint URL: {osticket.endpoint_url}")
print()

# Update to use Google OAuth2
print("Updating configuration...")
osticket.provider = 'google'
osticket.api_auth_type = 'oauth2'
osticket.save()

print("Configuration updated!")
print()
print("="*60)
print("OSTicket Endpoint Configuration:")
print("="*60)
print(f"  ID: {osticket.id}")
print(f"  Provider: {osticket.provider}")
print(f"  API Auth Type: {osticket.api_auth_type}")
print(f"  Endpoint URL: {osticket.endpoint_url}")
print(f"  Trigger Path: {osticket.trigger_path}")
print()

# Check if user has Google OAuth2 token
user = User.objects.filter(email='mikeoliveraz@gmail.com').first()
if not user:
    user = User.objects.filter(username__icontains='olient').first()

if user:
    print(f"Checking OAuth2 token for user: {user.username} ({user.email})")
    from allauth.socialaccount.models import SocialToken, SocialAccount

    try:
        social_account = SocialAccount.objects.get(user=user, provider='google')
        token = SocialToken.objects.get(account=social_account, app__provider='google')
        print(f"  OAuth2 token found: {token.token[:20]}...")
        print(f"  Token expires: {token.expires_at}")
        print("  OAuth2 authentication is ready!")
    except SocialToken.DoesNotExist:
        print("  WARNING: No Google OAuth2 token found for this user")
        print("  User needs to authenticate with Google first at /accounts/google/login/")
    except SocialAccount.DoesNotExist:
        print("  WARNING: No Google social account found for this user")
        print("  User needs to connect Google account first")
else:
    print("WARNING: User with email mikeoliveraz@gmail.com not found")

print()
print("="*60)
print("Next Steps:")
print("="*60)
print("1. The OSTicket endpoint is now configured to use Google OAuth2")
print("2. The osticket_admin_view needs to be updated to use OAuth2 tokens")
print("3. User must have authenticated with Google to access OSTicket")
print()

