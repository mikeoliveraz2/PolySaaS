#!/usr/bin/env python
"""
Test the Gmail API error handling directly.
"""
import os
import sys
import django

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

def test_api_error_handling():
    """Test the _handle_api_error method directly"""
    from dose.services.gmail_proxy_service import GmailProxyService
    import requests

    print("=== Testing Gmail API Error Handling ===")

    # Create a mock 401 response
    class MockResponse:
        def __init__(self, status_code, json_data=None):
            self.status_code = status_code
            self._json_data = json_data or {}

        def json(self):
            return self._json_data

    # Test 401 error
    print("\n🧪 Testing 401 Unauthorized error...")
    mock_401_response = MockResponse(401, {
        'error': {
            'code': 401,
            'message': 'Request had invalid authentication credentials',
            'status': 'UNAUTHENTICATED'
        }
    })

    response = GmailProxyService._handle_api_error(mock_401_response)
    print(f"📊 Response status: {response.status_code}")
    print(f"📊 Response type: {type(response)}")

    if hasattr(response, 'content'):
        content = response.content.decode('utf-8') if isinstance(response.content, bytes) else str(response.content)
        if 'Re-authenticate with Google' in content:
            print("✅ Enhanced OAuth error page is working!")
            print("🔗 Found re-authentication button")
        else:
            print("❌ Enhanced error page not found")
            print(f"📄 Content sample: {content[:200]}...")
    else:
        print("❌ No content in response")

if __name__ == "__main__":
    test_api_error_handling()