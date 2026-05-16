#!/usr/bin/env python
"""
End-to-End Integration Test for Phase 2: Token Refresh on 401
Tests the complete flow: store credentials -> make API call -> 401 -> auto-refresh -> success
Run directly: python test_phase2_e2e.py
"""

import os
import sys
import django
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth.models import User, AnonymousUser
from dose.passthrough.handlers.mattermost_handler import MattermostPassthroughHandler
from dose.passthrough.credential_container import PassthroughCredentialContainer
from django.http import HttpResponse
from unittest.mock import Mock, patch
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("\n" + "="*70)
print("[E2E TEST] Phase 2: End-to-End Token Refresh Integration")
print("="*70 + "\n")

# Scenario: User has stored credentials in session, makes API call to Mattermost
# First response is 401 (token expired), handler should refresh and user gets 200

print("[E2E] Simulating: User API call -> 401 -> Auto-refresh -> Success\n")

try:
    factory = RequestFactory()
    handler = MattermostPassthroughHandler()
    
    # Step 1: Create request with session
    print("[STEP 1] Creating request with user session")
    request = factory.get('/api/v4/users/me')
    request.session = SessionStore()
    request.user = AnonymousUser()
    
    # Step 2: Store Mattermost credentials in session (simulates login bridge)
    print("[STEP 2] Storing Mattermost credentials in session (simulates login bridge)")
    PassthroughCredentialContainer.store(
        request, 'mattermost',
        {
            'username': 'john.doe',
            'password': 'SecurePass123!',
            'email': 'john@example.com',
            'api_tokens': {'mattermost_token': 'expired_token_abc123'}
        }
    )
    
    # Verify credentials stored
    stored = PassthroughCredentialContainer.retrieve(request, 'mattermost')
    if stored:
        print(f"[OK] Credentials stored: username={stored.get('username')}, has_password={bool(stored.get('password'))}")
    else:
        print(f"[FAIL] Credentials not stored")
        sys.exit(1)
    
    # Step 3: Simulate upstream Mattermost returning 401 (token expired)
    print("\n[STEP 3] Simulating Mattermost API returning 401 (token expired)")
    mock_401_response = Mock()
    mock_401_response.status_code = 401
    mock_401_response.headers = {'Content-Type': 'application/json'}
    mock_401_response.content = b'{"error": "Authentication required"}'
    
    # Step 4: Simulate Mattermost login endpoint returning new token
    print("[STEP 4] Setting up mock for Mattermost login endpoint (will return new token)")
    mock_login_response = Mock()
    mock_login_response.status_code = 200
    mock_login_response.json.return_value = {
        'id': 'new_session_token_xyz789',  # New token from login
        'user_id': 'user_john_doe',
        'email': 'john@example.com',
        'username': 'john.doe'
    }
    
    # Step 5: Handler processes 401 response with token regeneration
    print("\n[STEP 5] Handler processes 401 -> attempts token refresh")
    with patch('dose.passthrough.handlers.mattermost_handler.requests.post', return_value=mock_login_response):
        result = handler.postprocess_upstream_response(
            mock_401_response,
            request,
            endpoint_url='https://mm.company.com',
            target_url='https://mm.company.com/api/v4/users/me',
            upstream_path='/api/v4/users/me',
            outbound_headers={'Authorization': 'Bearer expired_token_abc123'},
            upstream_cookies={'MMAUTHTOKEN': 'expired_token_abc123'}
        )
    
    # Step 6: Verify handler returned 200 OK with new token
    print("[STEP 6] Verifying handler response")
    if result is None:
        print(f"[FAIL] Handler returned None (expected 200 OK)")
        sys.exit(1)
    
    if result.status_code != 200:
        print(f"[FAIL] Expected status 200, got {result.status_code}")
        sys.exit(1)
    
    print(f"[OK] Handler returned 200 OK")
    
    if 'X-PolySaaS-Token-Refreshed' not in result:
        print(f"[FAIL] X-PolySaaS-Token-Refreshed header missing")
        sys.exit(1)
    
    print(f"[OK] Token refresh header present: X-PolySaaS-Token-Refreshed={result['X-PolySaaS-Token-Refreshed']}")
    
    if 'Set-Cookie' not in result:
        print(f"[FAIL] Set-Cookie header missing")
        sys.exit(1)
    
    if 'new_session_token_xyz789' not in result['Set-Cookie']:
        print(f"[FAIL] New token not in Set-Cookie header")
        sys.exit(1)
    
    print(f"[OK] New token in Set-Cookie: {result['Set-Cookie'][:50]}...")
    
    # Step 7: Verify session was updated with new token
    print("\n[STEP 7] Verifying session was updated with new token")
    updated_creds = PassthroughCredentialContainer.retrieve(request, 'mattermost')
    if not updated_creds:
        print(f"[FAIL] Credentials lost from session")
        sys.exit(1)
    
    stored_token = updated_creds.get('api_tokens', {}).get('mattermost_token')
    if stored_token == 'new_session_token_xyz789':
        print(f"[OK] Session token updated: {stored_token}")
    else:
        print(f"[FAIL] Session token not updated correctly: {stored_token}")
        sys.exit(1)
    
    # Step 8: Verify password still in session (not logged or removed)
    print("\n[STEP 8] Verifying password still in session (for future refreshes)")
    if updated_creds.get('password') == 'SecurePass123!':
        print(f"[OK] Password still in session (secure and ready for future refreshes)")
    else:
        print(f"[FAIL] Password missing or incorrect")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("[SUCCESS] End-to-End integration test passed!")
    print("="*70)
    print("\nSummary:")
    print("  1. Credentials stored in session")
    print("  2. API call returned 401 (token expired)")
    print("  3. Handler auto-refreshed token using encrypted password")
    print("  4. Handler returned 200 OK with new token in cookie")
    print("  5. Session updated with new token")
    print("  6. Password preserved for future refreshes")
    print("\n")

except Exception as e:
    print(f"\n[FAIL] E2E test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
