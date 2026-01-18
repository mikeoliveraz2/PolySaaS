"""
Quick test for v0 handler - Shela's suggestion

This creates a simple test endpoint to verify the v0 handler works.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.http import HttpRequest
from django.contrib.auth.models import User
from dose.models import PassThroughEndpoint
from dose.passthrough_handlers.v0_handler import V0PassthroughHandler

def test_v0_handler():
    """Test the v0 handler with a mock request"""

    print("="*60)
    print("V0 HANDLER QUICK TEST")
    print("="*60)

    # Get v0 endpoint
    try:
        v0_endpoint = PassThroughEndpoint.objects.get(trigger_path='v0')
        print(f"✅ Found v0 endpoint: {v0_endpoint.trigger_path} → {v0_endpoint.endpoint_url}")
    except PassThroughEndpoint.DoesNotExist:
        print("❌ No v0 endpoint found. Create one with trigger_path='v0'")
        return

    # Create mock request
    request = HttpRequest()
    request.method = 'GET'
    request.path = '/pt/admin/v0/'
    request.META = {
        'HTTP_USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'HTTP_HOST': 'localhost:8000'
    }

    # Create handler
    handler = V0PassthroughHandler(v0_endpoint, request)

    print(f"✅ Handler created for endpoint: {handler.endpoint.trigger_path}")

    # Test endpoint detection
    if handler.should_handle():
        print("✅ Handler correctly identifies v0 endpoint")
    else:
        print("❌ Handler failed to identify v0 endpoint")
        return

    # Test URL construction
    target_url = handler.get_target_url(v0_endpoint.endpoint_url, None)
    print(f"✅ Target URL: {target_url}")

    base_url = handler.get_base_url(v0_endpoint.endpoint_url)
    print(f"✅ Base URL: {base_url}")

    print("\n🎯 Handler is ready! Test it by visiting: /pt/admin/v0/")
    print("   Check Django logs for [V0 HANDLER] and [V0 DEBUG] messages")
    print("   Check browser Network tab for assets loading from v0.dev")

if __name__ == "__main__":
    test_v0_handler()