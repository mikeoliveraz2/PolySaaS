#!/usr/bin/env python
"""
TDD-style test for OSTicket passthrough rewriting logic.

This script:
1. Fetches the actual OSTicket login page
2. Applies our rewriting logic
3. Verifies the output matches expectations

Run with: python test_osticket_rewriting.py
"""

import os
import sys
import django
import requests
from bs4 import BeautifulSoup

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from dose.models import PassThroughEndpoint
from dose.generic_passthrough_views_deprecated import GenericScraperPassthroughView

# Configuration
OSTICKET_URL = "https://oliverenterprises.app.saasify.cloud/scp/login.php"
PROXY_BASE = "/pt/admin/osticket"


def fetch_original_osticket_page():
    """Fetch the original OSTicket login page."""
    print("="*80)
    print("STEP 1: Fetching original OSTicket login page")
    print("="*80)

    session = requests.Session()
    response = session.get(OSTICKET_URL, verify=False, timeout=15)

    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Content length: {len(response.content)} bytes")
    print(f"Cookies received: {[c.name for c in session.cookies]}")

    return response.text, session


def extract_form_details(html):
    """Extract form details from HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    forms = soup.find_all('form')

    details = []
    for form in forms:
        action = form.get('action', '')
        csrf_input = form.find('input', {'name': '__CSRFToken__'})
        csrf_value = csrf_input.get('value', '') if csrf_input else None
        csrf_name = csrf_input.get('name', '') if csrf_input else None

        details.append({
            'action': action,
            'csrf_name': csrf_name,
            'csrf_value': csrf_value,
            'csrf_length': len(csrf_value) if csrf_value else 0
        })

    return details


def apply_rewriting(html, endpoint, request_path):
    """Apply our rewriting logic to HTML."""
    print("\n" + "="*80)
    print("STEP 2: Applying rewriting logic")
    print("="*80)

    view = GenericScraperPassthroughView()

    # Extract ext_path from request_path
    if request_path.startswith('/pt/'):
        parts = request_path.strip('/').split('/')
        ext_path = '/'.join(parts[3:]) if len(parts) > 3 else ''
    else:
        ext_path = ''

    # Strip scp/ prefix if endpoint URL includes it
    if '/scp/' in endpoint.endpoint_url or endpoint.endpoint_url.endswith('/scp'):
        if ext_path.startswith('scp/'):
            ext_path = ext_path[4:]
        elif ext_path == 'scp':
            ext_path = ''

    rewritten_html = view.rewrite_urls(html, endpoint, ext_path, request_path=request_path)

    return rewritten_html


def test_csrf_token_preservation(original_html, rewritten_html):
    """Test that CSRF token is preserved during rewriting."""
    print("\n" + "="*80)
    print("TEST 1: CSRF Token Preservation")
    print("="*80)

    original_details = extract_form_details(original_html)
    rewritten_details = extract_form_details(rewritten_html)

    if len(original_details) != len(rewritten_details):
        print(f"❌ FAIL: Form count mismatch - Original: {len(original_details)}, Rewritten: {len(rewritten_details)}")
        return False

    all_passed = True
    for i, (orig, rew) in enumerate(zip(original_details, rewritten_details)):
        print(f"\nForm {i+1}:")
        print(f"  Original action: {orig['action']}")
        print(f"  Rewritten action: {rew['action']}")
        print(f"  Original CSRF: {orig['csrf_name']} = {orig['csrf_value'][:50] if orig['csrf_value'] else 'None'}...")
        print(f"  Rewritten CSRF: {rew['csrf_name']} = {rew['csrf_value'][:50] if rew['csrf_value'] else 'None'}...")

        if orig['csrf_value'] != rew['csrf_value']:
            print(f"  [FAIL] CSRF token changed!")
            print(f"     Original: {orig['csrf_value']}")
            print(f"     Rewritten: {rew['csrf_value']}")
            all_passed = False
        else:
            print(f"  [PASS] CSRF token preserved")

    return all_passed


def test_form_action_rewriting(original_html, rewritten_html):
    """Test that form actions are correctly rewritten."""
    print("\n" + "="*80)
    print("TEST 2: Form Action Rewriting")
    print("="*80)

    original_details = extract_form_details(original_html)
    rewritten_details = extract_form_details(rewritten_html)

    all_passed = True
    for i, (orig, rew) in enumerate(zip(original_details, rewritten_details)):
        print(f"\nForm {i+1}:")
        print(f"  Original action: {orig['action']}")
        print(f"  Rewritten action: {rew['action']}")

        # Check if action was rewritten correctly
        if not orig['action'] or orig['action'] == '#' or orig['action'].strip() == '':
            # Empty action should be set to current path
            if rew['action'] != PROXY_BASE + '/scp/login.php':
                print(f"  ⚠️  WARNING: Empty action not rewritten to expected path")
        elif orig['action'].startswith('/scp'):
            # Should be rewritten to proxy path
            expected = PROXY_BASE + orig['action']
            if rew['action'] != expected:
                print(f"  ❌ FAIL: Action not rewritten correctly")
                print(f"     Expected: {expected}")
                print(f"     Got: {rew['action']}")
                all_passed = False
            else:
                print(f"  [PASS] Action correctly rewritten")
        elif not orig['action'].startswith(('http', '#', 'javascript:')):
            # Relative path should be rewritten
            if not rew['action'].startswith(PROXY_BASE):
                print(f"  ⚠️  WARNING: Relative action may not be rewritten correctly")
        else:
            print(f"  ℹ️  INFO: Action unchanged (absolute URL or special)")

    return all_passed


def test_no_double_rewriting(rewritten_html):
    """Test that we don't have double-rewritten paths."""
    print("\n" + "="*80)
    print("TEST 3: No Double Rewriting")
    print("="*80)

    soup = BeautifulSoup(rewritten_html, 'html.parser')
    forms = soup.find_all('form')

    issues = []
    for form in forms:
        action = form.get('action', '')
        # Check for double /pt/admin/osticket
        if action.count('/pt/admin/osticket') > 1:
            issues.append(f"Double proxy base in action: {action}")
        # Check for /scp/scp/
        if '/scp/scp/' in action:
            issues.append(f"Double /scp/ in action: {action}")

    if issues:
        print("[FAIL] Found double rewriting issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("[PASS] No double rewriting detected")
        return True


def test_csrf_token_format(rewritten_html):
    """Test that CSRF token has correct format."""
    print("\n" + "="*80)
    print("TEST 4: CSRF Token Format")
    print("="*80)

    soup = BeautifulSoup(rewritten_html, 'html.parser')
    forms = soup.find_all('form')

    all_passed = True
    for i, form in enumerate(forms):
        csrf_input = form.find('input', {'name': '__CSRFToken__'})
        if csrf_input:
            csrf_value = csrf_input.get('value', '')
            print(f"\nForm {i+1} CSRF token:")
            print(f"  Name: {csrf_input.get('name')}")
            print(f"  Value length: {len(csrf_value)}")
            print(f"  Value preview: {csrf_value[:50]}...")

            # OSTicket CSRF tokens are typically 32-64 characters
            if len(csrf_value) < 10:
                print(f"  [FAIL] CSRF token too short (likely empty or corrupted)")
                all_passed = False
            elif len(csrf_value) > 200:
                print(f"  ⚠️  WARNING: CSRF token unusually long")
            else:
                print(f"  [PASS] CSRF token format looks correct")
        else:
            print(f"\nForm {i+1}: [FAIL] No CSRF token found!")
            all_passed = False

    return all_passed


def test_link_rewriting(original_html, rewritten_html):
    """Test that links are correctly rewritten."""
    print("\n" + "="*80)
    print("TEST 5: Link Rewriting")
    print("="*80)

    original_soup = BeautifulSoup(original_html, 'html.parser')
    rewritten_soup = BeautifulSoup(rewritten_html, 'html.parser')

    original_links = original_soup.find_all('a', href=True)
    rewritten_links = rewritten_soup.find_all('a', href=True)

    print(f"Original links: {len(original_links)}")
    print(f"Rewritten links: {len(rewritten_links)}")

    all_passed = True
    for i, (orig_link, rew_link) in enumerate(zip(original_links[:10], rewritten_links[:10])):  # Test first 10
        orig_href = orig_link.get('href', '')
        rew_href = rew_link.get('href', '')

        if orig_href.startswith('/scp'):
            expected = PROXY_BASE + orig_href
            if rew_href != expected:
                print(f"  [FAIL] Link {i+1} not rewritten correctly")
                print(f"     Original: {orig_href}")
                print(f"     Expected: {expected}")
                print(f"     Got: {rew_href}")
                all_passed = False
            else:
                print(f"  [PASS] Link {i+1} correctly rewritten: {orig_href} -> {rew_href}")

    return all_passed


def test_asset_urls_unchanged(original_html, rewritten_html):
    """Test that asset URLs (CSS, JS, images) are not incorrectly rewritten."""
    print("\n" + "="*80)
    print("TEST 6: Asset URLs Not Incorrectly Rewritten")
    print("="*80)

    rewritten_soup = BeautifulSoup(rewritten_html, 'html.parser')

    # Check CSS links
    css_links = rewritten_soup.find_all('link', rel='stylesheet', href=True)
    issues = []
    for link in css_links:
        href = link.get('href', '')
        # CSS should either be absolute URL or already rewritten correctly
        # Should NOT have double /pt/admin/osticket
        if href.count('/pt/admin/osticket') > 1:
            issues.append(f"CSS link has double proxy base: {href}")

    # Check JS scripts
    js_scripts = rewritten_soup.find_all('script', src=True)
    for script in js_scripts:
        src = script.get('src', '')
        if src.count('/pt/admin/osticket') > 1:
            issues.append(f"JS script has double proxy base: {src}")

    # Check images
    images = rewritten_soup.find_all('img', src=True)
    for img in images:
        src = img.get('src', '')
        if src.count('/pt/admin/osticket') > 1:
            issues.append(f"Image has double proxy base: {src}")

    if issues:
        print("[FAIL] Found asset URL issues:")
        for issue in issues[:5]:  # Show first 5
            print(f"  - {issue}")
        return False
    else:
        print("[PASS] No asset URL rewriting issues detected")
        return True


def test_post_processing_fixes(rewritten_html):
    """Test that post-processing fixes any unrewritten paths."""
    print("\n" + "="*80)
    print("TEST 7: Post-Processing Fixes")
    print("="*80)

    # Check for any remaining /scp/ paths that should have been rewritten
    issues = []
    if 'action="/scp/' in rewritten_html:
        issues.append("Found unrewritten form action: action=\"/scp/\"")
    if 'href="/scp/' in rewritten_html:
        issues.append("Found unrewritten link: href=\"/scp/\"")
    if 'window.location="/scp/' in rewritten_html:
        issues.append("Found unrewritten JavaScript redirect: window.location=\"/scp/\"")

    if issues:
        print("[FAIL] Post-processing did not catch all unrewritten paths:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("[PASS] No unrewritten paths found (post-processing working)")
        return True


def test_session_cookie_handling(original_response, session):
    """Test that session cookies are properly handled."""
    print("\n" + "="*80)
    print("TEST 8: Session Cookie Handling")
    print("="*80)

    cookies = session.cookies
    print(f"Cookies in session: {[c.name for c in cookies]}")

    # OSTicket should set OSTSESSID
    if 'OSTSESSID' in cookies:
        ostsessid = cookies.get('OSTSESSID')
        # cookies.get() returns the cookie value (string), not the Cookie object
        ostsessid_value = ostsessid if isinstance(ostsessid, str) else ostsessid.value
        print(f"[PASS] OSTSESSID cookie present: {ostsessid_value[:50]}...")
        print(f"       Cookie length: {len(ostsessid_value)}")
        return True
    else:
        print("[FAIL] OSTSESSID cookie not found in session")
        return False


def test_multiple_forms(original_html, rewritten_html):
    """Test that multiple forms are all handled correctly."""
    print("\n" + "="*80)
    print("TEST 9: Multiple Forms Handling")
    print("="*80)

    original_details = extract_form_details(original_html)
    rewritten_details = extract_form_details(rewritten_html)

    if len(original_details) != len(rewritten_details):
        print(f"[FAIL] Form count mismatch: {len(original_details)} -> {len(rewritten_details)}")
        return False

    print(f"[PASS] Form count preserved: {len(original_details)} forms")

    # Check all forms have CSRF tokens
    all_have_csrf = all(d['csrf_value'] for d in rewritten_details)
    if all_have_csrf:
        print(f"[PASS] All {len(rewritten_details)} forms have CSRF tokens")
    else:
        print(f"[FAIL] Some forms missing CSRF tokens")
        return False

    return True


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("OSTicket Passthrough Rewriting - TDD Test Suite")
    print("="*80)

    # Get endpoint
    endpoint = PassThroughEndpoint.objects.filter(
        trigger_path__icontains='osticket',
        is_enabled=True
    ).first()

    if not endpoint:
        print("[ERROR] OSTicket endpoint not found in database")
        return

    print(f"\nUsing endpoint: {endpoint.trigger_path}")
    print(f"Endpoint URL: {endpoint.endpoint_url}")

    # Fetch original
    original_html, session = fetch_original_osticket_page()
    original_response = session.get(OSTICKET_URL, verify=False, timeout=15)

    # Apply rewriting
    request_path = f"{PROXY_BASE}/scp/login.php"
    rewritten_html = apply_rewriting(original_html, endpoint, request_path)

    # Run tests
    results = []

    results.append(("CSRF Token Preservation", test_csrf_token_preservation(original_html, rewritten_html)))
    results.append(("Form Action Rewriting", test_form_action_rewriting(original_html, rewritten_html)))
    results.append(("No Double Rewriting", test_no_double_rewriting(rewritten_html)))
    results.append(("CSRF Token Format", test_csrf_token_format(rewritten_html)))
    results.append(("Link Rewriting", test_link_rewriting(original_html, rewritten_html)))
    results.append(("Asset URLs Not Incorrectly Rewritten", test_asset_urls_unchanged(original_html, rewritten_html)))
    results.append(("Post-Processing Fixes", test_post_processing_fixes(rewritten_html)))
    results.append(("Session Cookie Handling", test_session_cookie_handling(original_response, session)))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())

