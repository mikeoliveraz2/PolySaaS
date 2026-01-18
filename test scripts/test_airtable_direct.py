"""
Direct Airtable Authentication Test
Bypasses all middleware and rewriting - just tests if we can authenticate directly
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

import requests
from allauth.socialaccount.models import SocialToken, SocialAccount
from django.contrib.auth import get_user_model

User = get_user_model()

def test_airtable_direct():
    print("=" * 80)
    print("DIRECT AIRTABLE AUTHENTICATION TEST")
    print("=" * 80)

    # Get the user (assuming you're logged in as olientAdmin)
    user = User.objects.filter(username='olientAdmin').first()
    if not user:
        print("ERROR: User 'olientAdmin' not found")
        return

    print(f"\nUser: {user.username} (ID: {user.id})")

    # Get Google token
    google_token_obj = SocialToken.objects.filter(
        account__user=user,
        account__provider='google'
    ).first()

    if not google_token_obj:
        print("ERROR: No Google token found for user")
        return

    google_token = google_token_obj.token
    print(f"Google token found: {google_token[:20]}...")

    # Get Google account info
    google_account = SocialAccount.objects.filter(
        user=user,
        provider='google'
    ).first()

    email = None
    if google_account:
        email = google_account.extra_data.get('email') or user.email
        print(f"Google email: {email}")

    # Create a session
    session = requests.Session()

    # Test 1: Visit Airtable home page with Google token in headers
    print("\n" + "=" * 80)
    print("TEST 1: Visit Airtable home page with Google token")
    print("=" * 80)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    # Try multiple ways to pass the Google token
    headers['Authorization'] = f'Bearer {google_token}'
    headers['X-Google-Token'] = google_token
    if email:
        headers['X-Google-Email'] = email

    print(f"\nRequesting: https://airtable.com/")
    print(f"Headers:")
    for key, value in headers.items():
        if 'token' in key.lower() or 'authorization' in key.lower():
            print(f"  {key}: {value[:30]}...")
        else:
            print(f"  {key}: {value}")

    try:
        response = session.get('https://airtable.com/', headers=headers, timeout=30, allow_redirects=True)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response URL: {response.url}")
        print(f"Cookies received: {len(response.cookies)}")

        if response.cookies:
            print("\nCookies from Airtable:")
            for cookie in response.cookies:
                print(f"  {cookie.name}: {cookie.value[:50]}... (domain={cookie.domain}, path={cookie.path})")

        # Check if authenticated (look for login indicators)
        text = response.text.lower()
        login_indicators = ['sign in', 'log in', 'sign up', 'create account', 'get started', 'try it now', 'book demo']
        has_login = any(indicator in text for indicator in login_indicators)

        authenticated_indicators = ['workspace', 'base', 'dashboard', 'create base', 'my bases']
        has_authenticated = any(indicator in text for indicator in authenticated_indicators)

        print(f"\nContent Analysis:")
        print(f"  Has login indicators: {has_login}")
        print(f"  Has authenticated indicators: {has_authenticated}")

        if has_authenticated and not has_login:
            print("\n[SUCCESS] Appears to be authenticated!")
        elif has_login:
            print("\n[FAILED] Still showing login page")
        else:
            print("\n[UNCLEAR] Can't determine authentication status from content")

        # Save response to file for inspection
        with open('airtable_home_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\nResponse saved to: airtable_home_response.html")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Try accessing a specific Airtable base/app
    print("\n" + "=" * 80)
    print("TEST 2: Access Airtable base with Google token")
    print("=" * 80)

    # Use the base ID from your endpoint
    base_id = "apphVcCZHGhbpVOa4"
    base_url = f"https://airtable.com/{base_id}"

    print(f"\nRequesting: {base_url}")

    try:
        response2 = session.get(base_url, headers=headers, timeout=30, allow_redirects=True)
        print(f"\nResponse Status: {response2.status_code}")
        print(f"Response URL: {response2.url}")
        print(f"Cookies in session: {len(session.cookies)}")

        # Check if authenticated
        text2 = response2.text.lower()
        has_login2 = any(indicator in text2 for indicator in login_indicators)
        has_authenticated2 = any(indicator in text2 for indicator in authenticated_indicators)

        print(f"\nContent Analysis:")
        print(f"  Has login indicators: {has_login2}")
        print(f"  Has authenticated indicators: {has_authenticated2}")

        if has_authenticated2 and not has_login2:
            print("\n[SUCCESS] Appears to be authenticated!")
        elif has_login2:
            print("\n[FAILED] Still showing login page")
        else:
            print("\n[UNCLEAR] Can't determine authentication status")

        # Save response
        with open('airtable_base_response.html', 'w', encoding='utf-8') as f:
            f.write(response2.text)
        print(f"\nResponse saved to: airtable_base_response.html")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: Try with cookies from previous requests
    print("\n" + "=" * 80)
    print("TEST 3: Summary of session cookies")
    print("=" * 80)

    print(f"\nTotal cookies in session: {len(session.cookies)}")
    for cookie in session.cookies:
        print(f"  {cookie.name}: domain={cookie.domain}, path={cookie.path}, secure={cookie.secure}")

    print("\n" + "=" * 80)
    print("DONE")
    print("=" * 80)

if __name__ == '__main__':
    test_airtable_direct()

