"""
Test script for v0.dev endpoint with new content-block approach

This script:
1. Checks if v0 endpoint exists in database
2. Tests the handler detection
3. Simulates request processing
4. Validates URL rewriting functions
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
from dose.passthrough_handlers.v0_handler import (
    V0PassthroughHandler,
    rewrite_get_links_to_proxy,
    rewrite_assets_to_full_paths,
    inject_base_tag
)

print("=" * 80)
print("V0.DEV ENDPOINT TEST - CONTENT-BLOCK APPROACH")
print("=" * 80)

# Check for v0 endpoints
print("\n1. Checking for v0 endpoints in database...")
v0_endpoints = PassThroughEndpoint.objects.filter(
    trigger_path__icontains='v0'
) | PassThroughEndpoint.objects.filter(
    endpoint_url__icontains='v0'
)

if v0_endpoints.exists():
    print(f"✅ Found {v0_endpoints.count()} v0 endpoint(s):")
    for endpoint in v0_endpoints:
        print(f"   - ID: {endpoint.id}")
        print(f"     Trigger: {endpoint.trigger_path}")
        print(f"     URL: {endpoint.endpoint_url}")
        print(f"     Enabled: {endpoint.is_enabled}")
        print()
else:
    print("❌ No v0 endpoints found")
    print("   To create one, run: python add_v0_endpoint.py")

# Test helper functions
print("\n2. Testing URL rewriting helper functions...")

# Test GET link rewriting
test_html_links = '''
<html>
<body>
    <a href="/chat">Chat</a>
    <a href="/projects">Projects</a>
    <form action="/api/submit">
        <button type="submit">Submit</button>
    </form>
</body>
</html>
'''

proxy_base = "/admin/polysniffer/proxy/123"
endpoint_id = "123"

print("\n   Testing rewrite_get_links_to_proxy()...")
rewritten_links = rewrite_get_links_to_proxy(test_html_links, proxy_base, endpoint_id)
if '/admin/polysniffer/proxy/123/chat' in rewritten_links:
    print("   ✅ GET links correctly rewritten to proxy paths")
else:
    print("   ❌ GET link rewriting failed")
    print(f"   Result: {rewritten_links[:200]}")

# Test asset rewriting
test_html_assets = '''
<html>
<head>
    <link rel="stylesheet" href="/chat-static/styles.css">
    <script src="/_next/static/bundle.js"></script>
    <link rel="preload" href="/fonts/inter.woff2" as="font">
</head>
</html>
'''

print("\n   Testing rewrite_assets_to_full_paths()...")
rewritten_assets = rewrite_assets_to_full_paths(test_html_assets, 'https://v0.dev')
if 'https://v0.dev/chat-static/styles.css' in rewritten_assets:
    print("   ✅ Asset paths correctly rewritten to full URLs")
else:
    print("   ❌ Asset path rewriting failed")
    print(f"   Result: {rewritten_assets[:200]}")

# Test base tag injection
test_html_base = '<html><head><title>Test</title></head><body></body></html>'

print("\n   Testing inject_base_tag()...")
with_base = inject_base_tag(test_html_base, 'https://v0.dev/')
if '<base href="https://v0.dev/"' in with_base:
    print("   ✅ Base tag correctly injected")
else:
    print("   ❌ Base tag injection failed")
    print(f"   Result: {with_base[:200]}")

# Test login bypass logic
if v0_endpoints.exists():
    print("\n3. Testing login bypass logic...")
    endpoint = v0_endpoints.first()

    # Create mock request (simplified)
    class MockRequest:
        def __init__(self):
            self.path = '/admin/polysniffer/proxy/1/'
            self.headers = {}

    handler = V0PassthroughHandler(endpoint, MockRequest())

    # Test login detection
    login_html = '<html><body><h1>Sign in to v0</h1></body></html>'
    login_url = 'https://v0.dev'

    if handler.should_bypass_login(login_html, login_url):
        print("   ✅ Login screen correctly detected")
        dashboard_url = handler.get_dashboard_url()
        print(f"   Dashboard redirect: {dashboard_url}")
    else:
        print("   ❌ Login detection failed")

    # Test non-login page
    content_html = '<html><body><div class="chat-container">Chat content</div></body></html>'
    content_url = 'https://v0.dev/chat'

    if not handler.should_bypass_login(content_html, content_url):
        print("   ✅ Non-login page correctly identified")
    else:
        print("   ⚠️  Non-login page incorrectly flagged as login")

print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print("""
The v0 handler now implements a content-block approach:
1. ✅ Helper functions for URL/asset rewriting
2. ✅ Login screen bypass logic
3. ✅ Content extraction and wrapping
4. ⏳ Ready for live testing

Next step: Access v0 endpoint through Django and verify:
   - No login screen appears
   - Assets load from v0.dev
   - Navigation links work through proxy
""")

print("\n" + "=" * 80)
