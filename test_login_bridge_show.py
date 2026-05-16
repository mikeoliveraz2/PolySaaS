#!/usr/bin/env python
"""
Quick test: Verify login bridge HTML is served when no MMAUTHTOKEN cookie exists
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth.models import AnonymousUser
from dose.passthrough.handlers.mattermost_handler import MattermostPassthroughHandler
from unittest.mock import Mock

print("\n" + "="*70)
print("[TEST] Verify Login Bridge HTML is Served")
print("="*70 + "\n")

try:
    factory = RequestFactory()
    handler = MattermostPassthroughHandler()
    
    # Scenario 1: Root path with NO token → should show login bridge
    print("[TEST 1] Root path (/pt/admin/mattermost/) with no MMAUTHTOKEN")
    request = factory.get('/pt/admin/mattermost/')
    request.session = SessionStore()
    request.user = AnonymousUser()
    request.tenant = Mock(schema_name='test_tenant')
    
    # Mock the endpoint
    endpoint = Mock()
    endpoint.endpoint_url = 'https://mm.company.com'
    
    response = handler.try_root_display_shell_response(request, endpoint, 'mattermost')
    
    if response:
        content = response.content.decode('utf-8') if isinstance(response.content, bytes) else response.content
        if 'Sign in to Mattermost' in content and '<input type="password"' in content:
            print("✓ Login bridge HTML served correctly!")
            print(f"  Response status: {response.status_code}")
            print(f"  Content-Type: {response.get('Content-Type', 'N/A')}")
            print(f"  HTML snippet: {content[:200]}...")
        else:
            print("✗ Response served but not login bridge HTML")
            print(f"  Content preview: {content[:200]}...")
    else:
        print("✗ No response returned (returned None)")
    
    # Scenario 2: /login?force=1 path with no token → should also show login bridge
    print("\n[TEST 2] /login?force=1 path with no token")
    request2 = factory.get('/pt/admin/mattermost/login?force=1')
    request2.session = SessionStore()
    request2.user = AnonymousUser()
    request2.tenant = Mock(schema_name='test_tenant')
    
    response2 = handler.try_root_display_shell_response(request2, endpoint, 'mattermost')
    
    if response2:
        content2 = response2.content.decode('utf-8') if isinstance(response2.content, bytes) else response2.content
        if 'Sign in to Mattermost' in content2:
            print("✓ Login bridge served for /login?force=1 path!")
            print(f"  Response status: {response2.status_code}")
        else:
            print("✗ Response served but not login bridge HTML")
    else:
        print("✗ No response returned (returned None)")
    
    # Scenario 3: Root path WITH token → should redirect to team channels
    print("\n[TEST 3] Root path with MMAUTHTOKEN present")
    request3 = factory.get('/pt/admin/mattermost/')
    request3.session = SessionStore()
    request3.user = AnonymousUser()
    request3.tenant = Mock(schema_name='test_tenant')
    request3.COOKIES['MMAUTHTOKEN'] = 'valid_token_abc123'
    
    response3 = handler.try_root_display_shell_response(request3, endpoint, 'mattermost')
    
    if response3:
        if response3.status_code in (301, 302, 303, 307, 308):
            print(f"✓ Redirect response returned (HTTP {response3.status_code})")
            print(f"  Location: {response3.get('Location', 'N/A')}")
        else:
            print(f"✗ Unexpected response status: {response3.status_code}")
    else:
        print("✗ No response returned")
    
    print("\n" + "="*70)
    print("[RESULT] All login bridge tests completed!")
    print("="*70 + "\n")

except Exception as e:
    print(f"[ERROR] Test failed with exception: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
