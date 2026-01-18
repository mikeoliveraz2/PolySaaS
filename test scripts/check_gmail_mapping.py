import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from allauth.socialaccount.models import SocialToken
from django.contrib.auth.models import User

USERNAME = 'olientAdmin'

try:
    user = User.objects.get(username=USERNAME)
    print(f"Found user: {user.username} (email: {user.email})")
    try:
        token_obj = SocialToken.objects.get(account__user=user, account__provider__iexact='google')
        oauth_token = token_obj.token
        print(f"OAuth token found for {USERNAME}.")
        headers = {'Authorization': f'Bearer {oauth_token}'}
        response = requests.get('https://gmail.googleapis.com/gmail/v1/users/me/profile', headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"Gmail account linked: {data.get('emailAddress')}")
            print("✅ Mapping is correct if this is mikeoliveraz@gmail.com.")
        else:
            print(f"❌ Failed to fetch Gmail profile: {response.text}")
            print("You may need to re-authenticate with Google.")
    except SocialToken.DoesNotExist:
        print(f"❌ No Google OAuth token found for user {USERNAME}.")
        print("Please log in as olientAdmin and re-authenticate with Google.")
except User.DoesNotExist:
    print(f"❌ User {USERNAME} not found.")
    print("Check your Django admin for user setup.")
