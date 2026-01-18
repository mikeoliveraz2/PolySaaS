#!/usr/bin/env python
"""
Test script to verify OSTicket handler processing
Compares native HTML with processed HTML to ensure all URLs are rewritten correctly
"""

import sys
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.passthrough_handlers.osticket_handler import OSTicketPassthroughHandler

def test_osticket_handler():
    """Test the OSTicket handler with native HTML"""

    # Read the native HTML
    native_html_path = os.path.join(os.path.dirname(__file__), 'dose', 'osticket', 'native_osticket.html')
    with open(native_html_path, 'r', encoding='utf-8') as f:
        native_html = f.read()

    print(f"Loaded native HTML: {len(native_html)} characters")

    # Create handler instance with mock endpoint and request
    mock_endpoint = type('MockEndpoint', (), {
        'trigger_path': 'osticket',
        'endpoint_url': 'https://polysaas.supportsystem.com/scp/login.php'
    })()

    mock_request = type('MockRequest', (), {})()

    handler = OSTicketPassthroughHandler(mock_endpoint, mock_request)

    # Process the HTML
    proxy_base = '/pt/admin/osticket/'
    processed_html = handler.process_html_simple(native_html, proxy_base)

    print(f"Processed HTML: {len(processed_html)} characters")

    # Check for key patterns that should be rewritten
    checks = [
        ('CSS links', 'href="css/', f'href="https://polysaas.supportsystem.com/css/'),
        ('JS links', 'src="/js/', f'src="https://polysaas.supportsystem.com/js/'),
        ('Image links', 'src="../images/', f'src="https://polysaas.supportsystem.com/images/'),
        ('Form actions', 'action="login.php"', f'action="{proxy_base}login.php"'),
        ('Navigation links', 'href="index.php"', f'href="{proxy_base}index.php"'),
        ('Logo scripts', 'src="logo.php', f'src="https://polysaas.supportsystem.com/logo.php'),
    ]

    print("\n=== URL REWRITING CHECKS ===")
    all_passed = True

    for description, original_pattern, expected_replacement in checks:
        if original_pattern in native_html:
            if expected_replacement in processed_html:
                print(f"✅ {description}: PASS")
            else:
                print(f"❌ {description}: FAIL - Expected '{expected_replacement}' not found")
                all_passed = False
        else:
            print(f"⚠️  {description}: SKIPPED - Pattern '{original_pattern}' not in native HTML")

    # Check that problematic handlers are removed
    if 'onsubmit="attemptLoginAjax(event)"' not in processed_html:
        print("✅ Problematic onsubmit handler: REMOVED")
    else:
        print("❌ Problematic onsubmit handler: STILL PRESENT")
        all_passed = False

    # Check that our custom script is injected
    if 'OSTicket login fix script loaded' in processed_html:
        print("✅ Custom login script: INJECTED")
    else:
        print("❌ Custom login script: MISSING")
        all_passed = False

    print(f"\n=== OVERALL RESULT ===")
    if all_passed:
        print("🎉 ALL TESTS PASSED! Handler is working correctly.")
    else:
        print("❌ SOME TESTS FAILED! Handler needs fixes.")

    return all_passed

if __name__ == '__main__':
    success = test_osticket_handler()
    sys.exit(0 if success else 1)