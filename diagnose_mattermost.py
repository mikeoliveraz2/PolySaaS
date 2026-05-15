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

print()
print("="*60)
print("DIAGNOSIS:")
if not TOKEN:
    print("  FAIL: MATTERMOST_ADMIN_TOKEN is not set in Django settings")
elif r.status_code != 200:
    print(f"  FAIL: Token is invalid for this Mattermost instance (HTTP {r.status_code})")
else:
    print("  PASS: Token is valid and Mattermost is reachable")
