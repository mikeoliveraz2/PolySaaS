#!/usr/bin/env python
"""
Test PassthroughCredentialContainer encryption and session storage.
Run directly: python test_credential_container.py
"""

import os
import sys
import django

# Add current directory to Python path so dose module can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory
from cryptography.fernet import Fernet
from dose.passthrough.credential_container import PassthroughCredentialContainer
import base64
import hashlib
from django.conf import settings
from datetime import datetime, timedelta

print("\n" + "="*60)
print("[TEST] PassthroughCredentialContainer")
print("="*60 + "\n")

# Test 1: Cipher creation
print("[TEST 1] Cipher creation from SECRET_KEY")
try:
    cipher = PassthroughCredentialContainer._get_cipher()
    print(f"✓ Cipher created successfully: {type(cipher).__name__}")
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 2: Encryption/Decryption roundtrip
print("\n[TEST 2] Encryption/Decryption roundtrip")
test_password = "SuperSecurePassword123!"
try:
    encrypted = PassthroughCredentialContainer._encrypt_field(test_password)
    print(f"✓ Encrypted: {encrypted[:30]}...")
    
    decrypted = PassthroughCredentialContainer._decrypt_field(encrypted)
    print(f"✓ Decrypted: {decrypted}")
    
    if decrypted == test_password:
        print("✓ Roundtrip successful: plaintext == decrypted")
    else:
        print(f"✗ Mismatch: {test_password!r} != {decrypted!r}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 3: Session storage and retrieval
print("\n[TEST 3] Session storage and retrieval")
try:
    # Create a mock request with session
    factory = RequestFactory()
    request = factory.get('/')
    request.session = SessionStore()
    
    credentials = {
        'username': 'testuser',
        'password': 'TestPassword123!',
        'email': 'test@example.com',
        'api_tokens': {
            'mattermost_token': 'abc123def456',
            'other_token': 'xyz789'
        }
    }
    
    # Store credentials
    PassthroughCredentialContainer.store(request, 'mattermost', credentials, ttl_hours=24)
    print(f"✓ Credentials stored in session")
    
    # Check session contains encrypted data
    session_data = request.session.get(PassthroughCredentialContainer.SESSION_KEY)
    if session_data:
        print(f"✓ Session data present")
        print(f"  - username: {session_data.get('username')} (plaintext)")
        print(f"  - password: {session_data.get('password', '')[:30]}... (encrypted)")
        print(f"  - email: {session_data.get('email')} (plaintext)")
        print(f"  - api_tokens count: {len(session_data.get('api_tokens', {}))}")
    else:
        print(f"✗ Session data not found")
        sys.exit(1)
    
    # Retrieve and verify decryption
    retrieved = PassthroughCredentialContainer.retrieve(request, 'mattermost')
    if retrieved:
        print(f"✓ Credentials retrieved from session")
        
        # Verify each field
        if retrieved.get('username') == credentials['username']:
            print(f"  ✓ username matches")
        else:
            print(f"  ✗ username mismatch: {retrieved.get('username')} != {credentials['username']}")
            sys.exit(1)
        
        if retrieved.get('password') == credentials['password']:
            print(f"  ✓ password matches (decrypted successfully)")
        else:
            print(f"  ✗ password mismatch")
            sys.exit(1)
        
        if retrieved.get('email') == credentials['email']:
            print(f"  ✓ email matches")
        else:
            print(f"  ✗ email mismatch")
            sys.exit(1)
        
        # Check tokens
        tokens = retrieved.get('api_tokens', {})
        if tokens.get('mattermost_token') == 'abc123def456':
            print(f"  ✓ mattermost_token matches (decrypted successfully)")
        else:
            print(f"  ✗ mattermost_token mismatch: {tokens.get('mattermost_token')}")
            sys.exit(1)
    else:
        print(f"✗ Failed to retrieve credentials")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: App name validation
print("\n[TEST 4] App name validation (should return empty dict for wrong app)")
try:
    wrong_app = PassthroughCredentialContainer.retrieve(request, 'nextcloud')
    if wrong_app == {}:
        print(f"✓ Wrong app_name returns empty dict as expected")
    else:
        print(f"✗ Wrong app_name should return empty dict, got: {wrong_app}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 5: Expiry validation
print("\n[TEST 5] Expiry validation (expired credentials)")
try:
    # Store with very short TTL
    factory = RequestFactory()
    request2 = factory.get('/')
    request2.session = SessionStore()
    
    PassthroughCredentialContainer.store(
        request2, 'mattermost',
        credentials,
        ttl_hours=0  # Expires immediately
    )
    
    # Manually set expiry to past
    session_data = request2.session.get(PassthroughCredentialContainer.SESSION_KEY)
    session_data['expires_at'] = (datetime.now() - timedelta(hours=1)).isoformat()
    request2.session.modified = True
    
    # Try to retrieve
    retrieved = PassthroughCredentialContainer.retrieve(request2, 'mattermost')
    if retrieved == {}:
        print(f"✓ Expired credentials return empty dict")
    else:
        print(f"✗ Expired credentials should return empty dict, got: {retrieved}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Clear credentials
print("\n[TEST 6] Clear credentials from session")
try:
    factory = RequestFactory()
    request3 = factory.get('/')
    request3.session = SessionStore()
    
    PassthroughCredentialContainer.store(request3, 'mattermost', credentials, ttl_hours=24)
    print(f"✓ Credentials stored")
    
    PassthroughCredentialContainer.clear(request3)
    print(f"✓ Credentials cleared")
    
    retrieved = PassthroughCredentialContainer.retrieve(request3)
    if retrieved == {}:
        print(f"✓ After clear, retrieve returns empty dict")
    else:
        print(f"✗ After clear, should return empty dict, got: {retrieved}")
        sys.exit(1)
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("[SUCCESS] All tests passed!")
print("="*60 + "\n")
