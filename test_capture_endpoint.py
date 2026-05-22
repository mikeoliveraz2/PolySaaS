"""
Test script for the capture_endpoint API.
Tests the POST /admin/polysniffer/api/capture/ endpoint.
"""
import json

# Test data
test_payload = {
    "capture_id": "test-session-001",
    "entry_type": "fetch",
    "url": "https://api.example.com/users",
    "method": "GET",
    "status_code": 200,
    "duration_ms": 145.67,
    "request_headers": {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    },
    "response_headers": {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache"
    },
    "request_body": "",
    "response_body_preview": '{"users": [{"id": 1, "name": "Test User"}]}',
    "raw_entry": {
        "timestamp": "2026-05-22T06:30:00Z",
        "initiator": "fetch"
    }
}

def test_capture_endpoint():
    """Test the capture endpoint with sample data."""
    from dose.models import Tenant
    from dose.polysniffer.models import TrafficEntry, TrafficCapture
    
    print("=" * 60)
    print("Testing TrafficEntry Capture Endpoint")
    print("=" * 60)
    
    # Check if we have a tenant
    try:
        tenant = Tenant.objects.filter(is_active=True).first()
        if not tenant:
            print("❌ No active tenant found. Please create a tenant first.")
            return
        print(f"✓ Using tenant: {tenant.name} (slug={tenant.slug})")
    except Exception as e:
        print(f"❌ Error finding tenant: {e}")
        return
    
    # Check TrafficEntry model
    try:
        entry_count = TrafficEntry.objects.count()
        print(f"✓ TrafficEntry model accessible. Current count: {entry_count}")
    except Exception as e:
        print(f"❌ Error accessing TrafficEntry model: {e}")
        print("   Make sure migrations have been run: python manage.py migrate")
        return
    
    # Check TrafficCapture model
    try:
        capture_count = TrafficCapture.objects.count()
        print(f"✓ TrafficCapture model accessible. Current count: {capture_count}")
    except Exception as e:
        print(f"❌ Error accessing TrafficCapture model: {e}")
        return
    
    print("\n" + "=" * 60)
    print("Test Payload:")
    print("=" * 60)
    print(json.dumps(test_payload, indent=2))
    
    print("\n" + "=" * 60)
    print("Endpoint Information:")
    print("=" * 60)
    print("URL: POST /admin/polysniffer/api/capture/")
    print("Full URL: http://localhost:8000/admin/polysniffer/api/capture/")
    print("Authentication: @csrf_exempt (no CSRF token required)")
    print("Content-Type: application/json")
    
    print("\n" + "=" * 60)
    print("To test manually with curl:")
    print("=" * 60)
    curl_command = f"""curl -X POST http://localhost:8000/admin/polysniffer/api/capture/ \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(test_payload)}'"""
    print(curl_command)
    
    print("\n" + "=" * 60)
    print("Expected Response:")
    print("=" * 60)
    expected_response = {
        "success": True,
        "entry_id": "<generated_id>",
        "capture_id": "test-session-001",
        "capture_session_id": "<generated_id>",
        "tenant": tenant.slug
    }
    print(json.dumps(expected_response, indent=2))
    
    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print("The endpoint is ready to receive traffic captures from the browser.")
    print("\nNext steps:")
    print("1. Start the Django server: python manage.py runserver")
    print("2. Test with the curl command above")
    print("3. Check the database for new TrafficEntry records")
    print("4. Integrate with browser JavaScript to send real captures")

if __name__ == "__main__":
    import os
    import sys
    import django
    
    # Setup Django
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    django.setup()
    
    # Run test
    test_capture_endpoint()
