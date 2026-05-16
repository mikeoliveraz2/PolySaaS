#!/usr/bin/env python
"""
Test Phase 2: Token Refresh on 401
Tests the _regenerate_mattermost_token() method and postprocess_upstream_response() logic.
Run directly: python test_phase2_token_refresh.py
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.backends.db import SessionStore
from dose.passthrough.handlers.mattermost_handler import MattermostPassthroughHandler
from dose.passthrough.credential_container import PassthroughCredentialContainer
from unittest.mock import Mock, patch, MagicMock
import json

print("\n" + "="*60)
print("[TEST] Phase 2: Token Refresh on 401")
print("="*60 + "\n")

# Test 1: _regenerate_mattermost_token with successful login
print("[TEST 1] Token regeneration success path")
try:
    handler = MattermostPassthroughHandler()
    factory = RequestFactory()
    request = factory.get('/')
    request.session = SessionStore()
    
    # Mock the Mattermost login endpoint
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'id': 'new_session_token_12345',
        'user_id': 'user_abc123',
    }
    
    with patch('dose.passthrough.handlers.mattermost_handler.requests.post', return_value=mock_response):
        # First store credentials in session
        PassthroughCredentialContainer.store(
            request, 'mattermost',
            {
                'username': 'testuser',
                'password': 'TestPass123!',
                'email': 'test@example.com',
                'api_tokens': {'mattermost_token': 'old_token'}
            }
        )
        
        # Call with mm_url parameter
        new_token = handler._regenerate_mattermost_token(request, 'testuser', 'TestPass123!', mm_url='https://mm.example.com')
        
        if new_token == 'new_session_token_12345':
            print(f"[OK] Token regenerated: {new_token}")
        else:
            print(f"[FAIL] Expected 'new_session_token_12345', got {new_token}")
            sys.exit(1)
        
        # Verify session was updated with new token
        updated_creds = PassthroughCredentialContainer.retrieve(request, 'mattermost')
        if updated_creds.get('api_tokens', {}).get('mattermost_token') == 'new_session_token_12345':
            print(f"[OK] Session updated with new token")
        else:
            print(f"[FAIL] Session not updated")
            sys.exit(1)
            
except Exception as e:
    print(f"[FAIL] Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Token regeneration failure
print("\n[TEST 2] Token regeneration failure (invalid credentials)")
try:
    handler = MattermostPassthroughHandler()
    factory = RequestFactory()
    request = factory.get('/')
    request.session = SessionStore()
    
    # Mock failed login response
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.text = 'Invalid login credentials'
    
    with patch('dose.passthrough.handlers.mattermost_handler.requests.post', return_value=mock_response):
        new_token = handler._regenerate_mattermost_token(request, 'baduser', 'wrongpass', mm_url='https://mm.example.com')
        
        if new_token is None:
            print(f"[OK] Failed login returns None as expected")
        else:
            print(f"[FAIL] Expected None, got {new_token}")
            sys.exit(1)
            
except Exception as e:
    print(f"[FAIL] Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: postprocess_upstream_response with 401 and session credentials
print("\n[TEST 3] postprocess_upstream_response: 401 with token refresh")
try:
    handler = MattermostPassthroughHandler()
    factory = RequestFactory()
    request = factory.get('/')
    request.session = SessionStore()
    
    # Store credentials in session
    PassthroughCredentialContainer.store(
        request, 'mattermost',
        {
            'username': 'testuser',
            'password': 'TestPass123!',
            'email': 'test@example.com',
            'api_tokens': {'mattermost_token': 'expired_token'}
        }
    )
    
    # Mock 401 response from Mattermost
    mock_401_response = Mock()
    mock_401_response.status_code = 401
    mock_401_response.headers = {'Content-Type': 'application/json'}
    mock_401_response.content = b'{"error": "Unauthorized"}'
    
    # Mock successful token regeneration
    mock_login_response = Mock()
    mock_login_response.status_code = 200
    mock_login_response.json.return_value = {
        'id': 'refreshed_token_67890',
        'user_id': 'user_abc123',
    }
    
    with patch('dose.passthrough.handlers.mattermost_handler.requests.post', return_value=mock_login_response):
        result = handler.postprocess_upstream_response(
            mock_401_response,
            request,
            endpoint_url='https://mm.example.com',
            target_url='https://mm.example.com/api/v4/users/me',
            upstream_path='/api/v4/users/me',
            outbound_headers={},
            upstream_cookies={}
        )
        
        if result and result.status_code == 200:
            print(f"[OK] Postprocess returned 200 OK with token refresh")
            if 'X-PolySaaS-Token-Refreshed' in result:
                print(f"[OK] Token refresh header present")
            else:
                print(f"[FAIL] Token refresh header missing")
                sys.exit(1)
        else:
            print(f"[FAIL] Expected 200 response, got {result}")
            sys.exit(1)
            
except Exception as e:
    print(f"[FAIL] Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: postprocess_upstream_response with 401 but no session credentials
print("\n[TEST 4] postprocess_upstream_response: 401 without session (fallback clear)")
try:
    handler = MattermostPassthroughHandler()
    factory = RequestFactory()
    request = factory.get('/')
    request.session = SessionStore()
    # Note: NOT storing credentials in session
    
    # Mock 401 response
    mock_401_response = Mock()
    mock_401_response.status_code = 401
    mock_401_response.headers = {'Content-Type': 'application/json'}
    mock_401_response.content = b'{"error": "Unauthorized"}'
    
    # Mock _get_tenantapp_extra_config to return a config dict
    extra_config = {'mm_token': 'stale_token', 'mm_username': 'user'}
    
    with patch.object(handler, '_get_tenantapp_extra_config', return_value=extra_config):
        with patch.object(handler, '_save_tenantapp_config'):
            result = handler.postprocess_upstream_response(
                mock_401_response,
                request,
                endpoint_url='https://mm.example.com',
                target_url='https://mm.example.com/api/v4/users/me',
                upstream_path='/api/v4/users/me',
                outbound_headers={},
                upstream_cookies={}
            )
        
        if result and result.status_code == 401:
            print(f"[OK] Postprocess returned 401 with clear cookie header")
            if 'Set-Cookie' in result and 'MMAUTHTOKEN=' in result['Set-Cookie']:
                print(f"[OK] Cookie clear header present")
            else:
                print(f"[FAIL] Cookie clear header missing")
                sys.exit(1)
        else:
            print(f"[FAIL] Expected 401 response, got {result}")
            sys.exit(1)
            
except Exception as e:
    print(f"[FAIL] Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: No 401 response passes through
print("\n[TEST 5] postprocess_upstream_response: 200 OK passes through")
try:
    handler = MattermostPassthroughHandler()
    factory = RequestFactory()
    request = factory.get('/')
    request.session = SessionStore()
    
    # Mock 200 response
    mock_200_response = Mock()
    mock_200_response.status_code = 200
    mock_200_response.headers = {'Content-Type': 'application/json'}
    
    result = handler.postprocess_upstream_response(
        mock_200_response,
        request,
        endpoint_url='https://mm.example.com',
        target_url='https://mm.example.com/api/v4/users/me',
        upstream_path='/api/v4/users/me',
        outbound_headers={},
        upstream_cookies={}
    )
    
    if result is None:
        print(f"[OK] 200 OK returns None (pass through)")
    else:
        print(f"[FAIL] Expected None, got {result}")
        sys.exit(1)
        
except Exception as e:
    print(f"[FAIL] Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("[SUCCESS] All Phase 2 token refresh tests passed!")
print("="*60 + "\n")
