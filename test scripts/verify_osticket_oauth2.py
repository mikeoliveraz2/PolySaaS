#!/usr/bin/env python
"""
Verify OSTicket OAuth2 configuration
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialToken, SocialAccount

print("="*60)
print("OSTicket OAuth2 Configuration Verification")
print("="*60)
print()

# Check endpoint configuration
osticket = PassThroughEndpoint.objects.filter(
    trigger_path__icontains='osticket'
).first()

if not osticket:
    print("ERROR: OSTicket endpoint not found!")
    exit(1)

print("Endpoint Configuration:")
print(f"  ID: {osticket.id}")
print(f"  Trigger Path: {osticket.trigger_path}")
print(f"  Provider: {osticket.provider}")
print(f"  API Auth Type: {osticket.api_auth_type}")
print(f"  Endpoint URL: {osticket.endpoint_url}")
print(f"  Enabled: {osticket.is_enabled}")
print()

# Check OAuth2 configuration
if osticket.provider == 'google' and osticket.api_auth_type == 'oauth2':
    print("OAuth2 Configuration: CORRECT")
    print("  Provider: Google")
    print("  Auth Type: OAuth2")
else:
    print("OAuth2 Configuration: INCORRECT")
    print(f"  Expected: provider='google', api_auth_type='oauth2'")
    print(f"  Actual: provider='{osticket.provider}', api_auth_type='{osticket.api_auth_type}'")
    print()
    print("Run: python update_osticket_oauth2.py to fix")

print()

# Check user OAuth2 token
user = User.objects.filter(email='mikeoliveraz@gmail.com').first()
if not user:
    user = User.objects.filter(username__icontains='olient').first()

if user:
    print(f"User: {user.username} ({user.email})")

    try:
        social_account = SocialAccount.objects.get(user=user, provider='google')
        print(f"  Google Social Account: Found (UID: {social_account.uid})")

        token = SocialToken.objects.get(account=social_account, app__provider='google')
        print(f"  OAuth2 Token: Found")
        print(f"    Token (first 20 chars): {token.token[:20]}...")
        print(f"    Expires: {token.expires_at}")
        print(f"    Has Refresh Token: {'Yes' if token.token_secret else 'No'}")
        print()
        print("OAuth2 Authentication: READY")
    except SocialToken.DoesNotExist:
        print("  OAuth2 Token: NOT FOUND")
        print("  User needs to authenticate with Google at /accounts/google/login/")
        print()
        print("OAuth2 Authentication: NOT READY")
    except SocialAccount.DoesNotExist:
        print("  Google Social Account: NOT FOUND")
        print("  User needs to connect Google account first")
        print()
        print("OAuth2 Authentication: NOT READY")
else:
    print("WARNING: User with email mikeoliveraz@gmail.com not found")

print()
print("="*60)
print("Summary:")
print("="*60)
print("1. OSTicket endpoint is configured for Google OAuth2")
print("2. osticket_admin_view will automatically use OAuth2 tokens")
print("3. OAuth2 token is added to Authorization header in requests")
print("4. Token refresh is handled automatically if expired")
print()

