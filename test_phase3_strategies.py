#!/usr/bin/env python
"""
Test Phase 3: Token Refresh Strategies
Tests all per-app token refresh strategies (Mattermost, Nextcloud, Odoo)
Run directly: python test_phase3_strategies.py
"""

import os
import sys
import django
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.backends.db import SessionStore
from dose.passthrough.credential_container import PassthroughCredentialContainer
from dose.passthrough.strategies import (
    TokenRefreshStrategyFactory,
    MattermostTokenRefreshStrategy,
    NextcloudTokenRefreshStrategy,
    OdooTokenRefreshStrategy
)
from unittest.mock import Mock, patch

print("\n" + "="*70)
print("[TEST] Phase 3: Token Refresh Strategies")
print("="*70 + "\n")

# TEST 1: Mattermost Strategy
print("[TEST 1] MattermostTokenRefreshStrategy")
try:
    factory = RequestFactory()
    request = factory.get('/')
    request.session = SessionStore()
    
    # Store credentials
    PassthroughCredentialContainer.store(
        request, 'mattermost',
        {
            'username': 'testuser',
            'password': 'TestPass123!',
            'email': 'test@example.com',
            'api_tokens': {'mattermost_token': 'old_token'}
        }
    )
    
    # Mock Mattermost login response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'id': 'mattermost_token_new_123',
        'user_id': 'user_abc'
    }
    
    strategy = MattermostTokenRefreshStrategy()
    
    with patch('dose.passthrough.strategies.mattermost_strategy.requests.post', return_value=mock_response):
        new_token = strategy.refresh(request, 'https://mm.example.com', 'testuser', 'TestPass123!')
    
    if new_token == 'mattermost_token_new_123':
        print("[OK] Mattermost strategy token refreshed")
    else:
        print(f"[FAIL] Expected token, got {new_token}")
        sys.exit(1)
    
    # Verify stored in session
    updated = PassthroughCredentialContainer.retrieve(request, 'mattermost')
    if updated.get('api_tokens', {}).get('mattermost_token') == 'mattermost_token_new_123':
        print("[OK] Token stored in session")
    else:
        print("[FAIL] Token not stored")
        sys.exit(1)
        
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# TEST 2: Nextcloud Strategy
print("\n[TEST 2] NextcloudTokenRefreshStrategy")
try:
    factory = RequestFactory()
    request = factory.get('/')
    request.session = SessionStore()
    
    # Store credentials
    PassthroughCredentialContainer.store(
        request, 'nextcloud',
        {
            'username': 'john.doe',
            'password': 'CloudPass456!',
            'email': 'john@example.com',
            'api_tokens': {'nextcloud_token': 'old_app_password'}
        }
    )
    
    # Mock Nextcloud app password creation response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'ocs': {
            'meta': {'status': 'ok'},
            'data': {
                'appPassword': 'nextcloud_apppass_xyz789'
            }
        }
    }
    
    strategy = NextcloudTokenRefreshStrategy()
    
    with patch('dose.passthrough.strategies.nextcloud_strategy.requests.post', return_value=mock_response):
        new_token = strategy.refresh(request, 'https://nc.example.com', 'john.doe', 'CloudPass456!')
    
    if new_token == 'nextcloud_apppass_xyz789':
        print("[OK] Nextcloud strategy app password created")
    else:
        print(f"[FAIL] Expected token, got {new_token}")
        sys.exit(1)
    
    # Verify stored in session
    updated = PassthroughCredentialContainer.retrieve(request, 'nextcloud')
    if updated.get('api_tokens', {}).get('nextcloud_token') == 'nextcloud_apppass_xyz789':
        print("[OK] App password stored in session")
    else:
        print("[FAIL] App password not stored")
        sys.exit(1)
        
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# TEST 3: Odoo Strategy
print("\n[TEST 3] OdooTokenRefreshStrategy")
try:
    factory = RequestFactory()
    request = factory.get('/')
    request.session = SessionStore()
    
    # Store credentials
    PassthroughCredentialContainer.store(
        request, 'odoo',
        {
            'username': 'admin',
            'password': 'OdooPass789!',
            'email': 'admin@example.com',
            'api_tokens': {'odoo_session_id': 'old_session'}
        }
    )
    
    # Mock Odoo session response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {
        'Set-Cookie': 'session_id=odoo_session_new_abc123def; Path=/'
    }
    
    strategy = OdooTokenRefreshStrategy(database_name='odoo_db')
    
    with patch('dose.passthrough.strategies.odoo_strategy.requests.Session') as MockSession:
        mock_session_instance = Mock()
        mock_session_instance.post.return_value = mock_response
        MockSession.return_value = mock_session_instance
        
        new_token = strategy.refresh(request, 'https://odoo.example.com', 'admin', 'OdooPass789!')
    
    if new_token == 'odoo_session_new_abc123def':
        print("[OK] Odoo strategy session ID created")
    else:
        print(f"[FAIL] Expected session ID, got {new_token}")
        sys.exit(1)
    
    # Verify stored in session
    updated = PassthroughCredentialContainer.retrieve(request, 'odoo')
    if updated.get('api_tokens', {}).get('odoo_session_id') == 'odoo_session_new_abc123def':
        print("[OK] Session ID stored in session")
    else:
        print("[FAIL] Session ID not stored")
        sys.exit(1)
        
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# TEST 4: Factory Get Strategy
print("\n[TEST 4] TokenRefreshStrategyFactory.get_strategy()")
try:
    # Test getting all strategies
    strategies = [
        ('mattermost', MattermostTokenRefreshStrategy),
        ('nextcloud', NextcloudTokenRefreshStrategy),
        ('odoo', OdooTokenRefreshStrategy),
    ]
    
    for app_type, expected_class in strategies:
        strategy = TokenRefreshStrategyFactory.get_strategy(app_type)
        if isinstance(strategy, expected_class):
            print(f"[OK] Got strategy for {app_type}: {strategy.__class__.__name__}")
        else:
            print(f"[FAIL] Wrong strategy type for {app_type}")
            sys.exit(1)
            
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# TEST 5: Factory Supported Types
print("\n[TEST 5] TokenRefreshStrategyFactory.get_supported_types()")
try:
    supported = TokenRefreshStrategyFactory.get_supported_types()
    
    required = {'mattermost', 'nextcloud', 'odoo'}
    if set(supported) >= required:
        print(f"[OK] All required types supported: {', '.join(supported)}")
    else:
        missing = required - set(supported)
        print(f"[FAIL] Missing types: {missing}")
        sys.exit(1)
        
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# TEST 6: Unknown App Type Error
print("\n[TEST 6] TokenRefreshStrategyFactory error handling")
try:
    try:
        strategy = TokenRefreshStrategyFactory.get_strategy('unknown_app')
        print("[FAIL] Should have raised ValueError for unknown app type")
        sys.exit(1)
    except ValueError as e:
        if 'Unknown app type' in str(e):
            print(f"[OK] Correct error for unknown app type")
        else:
            print(f"[FAIL] Wrong error: {e}")
            sys.exit(1)
            
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("[SUCCESS] All Phase 3 strategy tests passed!")
print("="*70 + "\n")
