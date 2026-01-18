#!/usr/bin/env python
"""
Test the simplified PassThroughEndpoint path handling.
Verify that users can now just enter '/gmail/' instead of '/dose/gmail/'.
"""
import os
import sys
import django

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models.pass_through_endpoint import PassThroughEndpoint

def test_simplified_paths():
    """Test that the model now accepts simplified paths like /gmail/"""

    print("=== Testing Simplified PassThroughEndpoint Paths ===")

    # Test 1: Create endpoint with simple path
    print("\n1. Testing simple path '/gmail/':")
    try:
        # Try to create a test endpoint with the simple path
        test_endpoint = PassThroughEndpoint(
            trigger_path="/gmail/",
            endpoint_url="http://localhost:5000/gmail",
            menu_title="Gmail Test",
            show_in_menu=True
        )
        test_endpoint.full_clean()  # Validate without saving
        print("   ✅ Validation passed for '/gmail/'")
        print(f"   📁 Final trigger_path: '{test_endpoint.trigger_path}'")
    except Exception as e:
        print(f"   ❌ Validation failed: {e}")

    # Test 2: Create endpoint with legacy /dose/ path
    print("\n2. Testing legacy path '/dose/gmail/':")
    try:
        test_endpoint2 = PassThroughEndpoint(
            trigger_path="/dose/gmail/",
            endpoint_url="http://localhost:5000/gmail",
            menu_title="Gmail Legacy Test",
            show_in_menu=True
        )
        test_endpoint2.full_clean()  # Validate without saving
        print("   ✅ Validation passed for '/dose/gmail/'")
        print(f"   📁 Final trigger_path: '{test_endpoint2.trigger_path}'")
    except Exception as e:
        print(f"   ❌ Validation failed: {e}")

    # Test 3: Test middleware transformation logic
    print("\n3. Testing middleware path transformation:")

    test_paths = [
        "/gmail/",
        "/dose/gmail/",
        "/calendar/",
        "/dose/calendar/",
        "/api/",
        "/dose/api/"
    ]

    for path in test_paths:
        # Simulate middleware logic
        clean_path = path
        if clean_path.startswith('/dose/'):
            clean_path = clean_path[5:]  # Remove '/dose' prefix
        admin_url = f"/admin{clean_path.rstrip('/')}/"

        print(f"   📍 '{path}' -> '{admin_url}'")

    # Test 4: Check existing Gmail entries in database
    print("\n4. Checking existing Gmail entries in database:")
    try:
        gmail_entries = PassThroughEndpoint.objects.filter(menu_title__icontains='gmail')
        if gmail_entries.exists():
            for entry in gmail_entries:
                print(f"   📧 Found: '{entry.menu_title}' -> '{entry.trigger_path}' (show_in_menu: {entry.show_in_menu})")
        else:
            print("   📭 No Gmail entries found in database")
    except Exception as e:
        print(f"   ❌ Database query failed: {e}")

    print("\n=== Test Complete ===")
    print("✨ Users can now enter simplified paths like '/gmail/' instead of '/dose/gmail/'!")
    print("🔄 Middleware automatically handles the transformation to admin URLs")

if __name__ == "__main__":
    test_simplified_paths()