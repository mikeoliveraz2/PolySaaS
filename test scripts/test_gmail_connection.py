import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from allauth.socialaccount.models import SocialToken
import requests

# Check Google tokens
tokens = SocialToken.objects.filter(account__provider='google')
print(f'Found {tokens.count()} Google tokens')

if tokens.exists():
    token = tokens.first()
    print(f'Token for {token.account.user.username}: exists')

    # Test Gmail API
    headers = {'Authorization': f'Bearer {token.token}'}
    try:
        response = requests.get(
            'https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=3',
            headers=headers,
            timeout=10
        )
        print(f'Gmail API status: {response.status_code}')

        if response.status_code == 200:
            data = response.json()
            message_count = len(data.get('messages', []))
            print(f'Found {message_count} messages')
            if message_count > 0:
                print('Gmail API is working!')
            else:
                print('Gmail API works but no messages found')
        else:
            print(f'Gmail API error: {response.text}')

    except Exception as e:
        print(f'Gmail API exception: {e}')
else:
    print('No Google tokens - user needs to authenticate with Google OAuth')