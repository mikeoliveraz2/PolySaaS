#!/usr/bin/env python
"""
Test script to verify if Early Fetch Guard is properly injected into Mattermost HTML.
"""

import requests
import re
import sys

def extract_guard_script(html):
    """Extract the Early Fetch Guard script from HTML."""
    pattern = r'<script data-polysaas-mm-fetch-guard="1">(.*?)</script>'
    match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(0)
    return None

def check_guard_implementation(script_html):
    """Check if the guard script has the expected functionality."""
    if not script_html:
        return False, "Guard script not found"
    
    checks = {
        "Fetch override": "window.fetch = function" in script_html,
        "XHR open override": "XMLHttpRequest.prototype.open" in script_html,
        "XHR send override": "XMLHttpRequest.prototype.send" in script_html,
        "Scheduled posts stub": "/api/v4/posts/scheduled/" in script_html,
        "Trial license stub": "/api/v4/trial-license/" in script_html,
        "Console message": "Early fetch guard installed" in script_html,
        "Token variable": "var _serverToken" in script_html,
        "Guard function": "function _mmGuardStub" in script_html,
    }
    
    all_ok = True
    for check_name, result in checks.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {check_name}")
        if not result:
            all_ok = False
    
    return all_ok, script_html

def extract_token_from_guard(script_html):
    """Extract and check the token passed to the guard."""
    pattern = r'var _serverToken = (".*?");'
    match = re.search(pattern, script_html, re.DOTALL)
    if match:
        token_value = match.group(1)
        try:
            import json
            token = json.loads(token_value)
            if token:
                token_len = len(token)
                is_valid = token_len > 8
                status = "[OK]" if is_valid else "[FAIL]"
                print(f"  {status} Token present and valid (len={token_len})")
                return token, is_valid
            else:
                print(f"  [FAIL] Token is empty string")
                return "", False
        except Exception as e:
            print(f"  [FAIL] Error parsing token: {e}")
            return None, False
    print(f"  [FAIL] Token variable not found in guard script")
    return None, False

def test_passthrough_url(url, cookie_value=None):
    """Test a passthrough URL and check for guard injection."""
    print("=" * 80)
    print(f"Testing URL: {url}")
    print("=" * 80)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0'
    }
    
    cookies = {}
    if cookie_value:
        cookies['sessionid'] = cookie_value
    
    try:
        print("\n1. Fetching HTML from passthrough URL...")
        response = requests.get(url, headers=headers, cookies=cookies, timeout=15, verify=False)
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        print(f"   Content-Length: {len(response.text)} bytes")
        
        if response.status_code != 200:
            print(f"   [FAIL] Got {response.status_code} instead of 200")
            if '<title>' in response.text:
                title_match = re.search(r'<title>(.*?)</title>', response.text)
                if title_match:
                    print(f"   Page title: {title_match.group(1)}")
            return False
        
        html = response.text
        print(f"   [OK] Got HTML response")
        
        print("\n2. Checking for Early Fetch Guard script...")
        guard_script = extract_guard_script(html)
        if guard_script:
            print(f"   [OK] Guard script found ({len(guard_script)} bytes)")
        else:
            print(f"   [FAIL] Guard script NOT FOUND in HTML")
            if '<head' in html.lower():
                print(f"   -> <head> tag is present, but guard not injected")
            else:
                print(f"   -> No <head> tag found either")
            return False
        
        print("\n3. Verifying guard implementation...")
        impl_ok, script = check_guard_implementation(guard_script)
        
        print("\n4. Checking token in guard...")
        token, token_ok = extract_token_from_guard(guard_script)
        
        if not impl_ok:
            print("\n   [FAIL] Guard implementation incomplete")
            return False
        
        if not token_ok:
            print("\n   [FAIL] Token missing or too short")
            return False
        
        print("\n5. Checking for display shim...")
        display_shim_pattern = r'<script data-polysaas-mattermost-shim="1">'
        if re.search(display_shim_pattern, html):
            print("   [OK] Display shim found")
        else:
            print("   [FAIL] Display shim NOT found")
            return False
        
        print("\n" + "=" * 80)
        print("[OK] ALL CHECKS PASSED - Guard is properly injected")
        print("=" * 80)
        return True
        
    except requests.exceptions.ConnectionError as e:
        print(f"   [FAIL] Connection error: {e}")
        print(f"   -> Is the Django dev server running on localhost:8000?")
        return False
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 80)
    print("MATTERMOST PASSTHROUGH - EARLY FETCH GUARD INJECTION TEST")
    print("=" * 80 + "\n")
    
    test_cases = [
        {
            "name": "User t150 (new subscriber)",
            "url": "http://localhost:8000/pt/admin/polysaas-mattermost.onrender.com/polysaas-test-150/channels/town-square",
        },
        {
            "name": "User t142 (existing)",
            "url": "http://localhost:8000/pt/admin/polysaas-mattermost.onrender.com/polysaas-test-142/channels/town-square",
        },
    ]
    
    results = []
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        print("-" * 80)
        success = test_passthrough_url(test_case['url'])
        results.append((test_case['name'], success))
        print("\n")
    
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    if all_passed:
        print("\n[OK] All tests passed - guard is properly injected for all users")
    else:
        print("\n[FAIL] Some tests failed - guard injection may have issues")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    sys.exit(main())
