#!/usr/bin/env python
"""Diagnose Mattermost connectivity and token validity."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django
django.setup()

import requests
from django.conf import settings

MM_URL = getattr(settings, 'MATTERMOST_URL', 'https://polysaas-mattermost.onrender.com').rstrip('/')
TOKEN = getattr(settings, 'MATTERMOST_ADMIN_TOKEN', '').strip()

print(f"Mattermost URL: {MM_URL}")
print(f"Token present: {bool(TOKEN)} (length={len(TOKEN)})")
print(f"Token preview: {TOKEN[:10]}...{TOKEN[-5:]}" if TOKEN else "NONE")
print()

# Test 1: Ping
print("="*60)
print("TEST 1: /api/v4/system/ping")
try:
    r = requests.get(f"{MM_URL}/api/v4/system/ping", timeout=10)
    print(f"  Status: {r.status_code}")
    print(f"  Body: {r.text[:200]}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 2: Token verification
print()
print("="*60)
print("TEST 2: /api/v4/users/me (token check)")
if TOKEN:
    try:
        r = requests.get(f"{MM_URL}/api/v4/users/me", headers={"Authorization": f"Bearer {TOKEN}"}, timeout=10)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            user = r.json()
            print(f"  Admin user: {user.get('username')}")
            print(f"  Roles: {user.get('roles', '')[:100]}")
            print(f"  System admin: {'system_admin' in user.get('roles', '')}")
        else:
            print(f"  Body: {r.text[:300]}")
    except Exception as e:
        print(f"  ERROR: {e}")
else:
    print("  SKIPPED: No token configured")

# Test 3: List teams
print()
print("="*60)
print("TEST 3: /api/v4/teams")
if TOKEN:
    try:
        r = requests.get(f"{MM_URL}/api/v4/teams", headers={"Authorization": f"Bearer {TOKEN}"}, timeout=10)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            teams = r.json()
            print(f"  Teams: {len(teams)}")
            for t in teams:
                print(f"    - {t['name']} (id={t['id'][:8]}...)")
        else:
            print(f"  Body: {r.text[:300]}")
    except Exception as e:
        print(f"  ERROR: {e}")
else:
    print("  SKIPPED: No token configured")

# Test 4: Server config — are personal access tokens enabled?
print()
print("="*60)
print("TEST 4: /api/v4/config/client — check if PATs enabled")
if TOKEN:
    try:
        r = requests.get(f"{MM_URL}/api/v4/config/client?format=old", headers={"Authorization": f"Bearer {TOKEN}"}, timeout=10)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            cfg = r.json()
            print(f"  EnableUserAccessTokens: {cfg.get('EnableUserAccessTokens', 'NOT FOUND')}")
            print(f"  SiteName: {cfg.get('SiteName', 'NOT FOUND')}")
            print(f"  SiteURL: {cfg.get('SiteURL', 'NOT FOUND')}")
        else:
            print(f"  Body: {r.text[:300]}")
    except Exception as e:
        print(f"  ERROR: {e}")
else:
    print("  SKIPPED: No token")

# Test 5: Login with username/password to verify credentials and get session token
print()
print("="*60)
print("TEST 5: Login with username/password")
print("  (Enter your Mattermost admin username and password)")
import getpass
mm_user = input("  Mattermost admin username: ").strip()
mm_pass = getpass.getpass("  Mattermost admin password: ")
session_token = None
if mm_user and mm_pass:
    try:
        r = requests.post(f"{MM_URL}/api/v4/users/login", json={"login_id": mm_user, "password": mm_pass}, timeout=10)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            session_token = r.headers.get('Token')
            user = r.json()
            print(f"  Logged in as: {user.get('username')}")
            print(f"  User ID: {user.get('id')}")
            print(f"  Roles: {user.get('roles', '')[:100]}")
            print(f"  Is System Admin: {'system_admin' in user.get('roles', '')}")
            print(f"  Session Token: {session_token[:10]}..." if session_token else "NONE")
        else:
            print(f"  Body: {r.text[:300]}")
    except Exception as e:
        print(f"  ERROR: {e}")
else:
    print("  SKIPPED: No credentials provided")

# Test 6: Create a new Personal Access Token using session token
print()
print("="*60)
print("TEST 6: Create new Personal Access Token via API")
if session_token:
    try:
        user_id = user.get('id')
        r = requests.post(
            f"{MM_URL}/api/v4/users/{user_id}/tokens",
            headers={"Authorization": f"Bearer {session_token}"},
            json={"description": "Provisioning token from diagnose script"},
            timeout=10
        )
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            token_data = r.json()
            print(f"  New token created: {token_data.get('token', 'N/A')[:15]}...")
            print(f"  Token ID: {token_data.get('id')}")
            print(f"  Description: {token_data.get('description')}")
            print(f"\n  ADD THIS TO YOUR .ENV AND RENDER VARS:")
            print(f"  MATTERMOST_ADMIN_TOKEN={token_data.get('token')}")
        else:
            print(f"  Body: {r.text[:300]}")
    except Exception as e:
        print(f"  ERROR: {e}")
else:
    print("  SKIPPED: No session token (login failed)")

print()
print("="*60)
print("DIAGNOSIS:")
if not TOKEN:
    print("  FAIL: MATTERMOST_ADMIN_TOKEN is not set in Django settings")
elif r.status_code != 200:
    print(f"  FAIL: Token is invalid for this Mattermost instance (HTTP {r.status_code})")
    print(f"  Most likely causes:")
    print(f"    1. Personal Access Tokens not enabled in Mattermost (check TEST 4)")
    print(f"    2. Token was created on a DIFFERENT Mattermost instance")
    print(f"    3. User who created token is not a System Admin")
    print(f"    4. Mattermost server was reset, invalidating all tokens")
else:
    print("  PASS: Token is valid and Mattermost is reachable")
