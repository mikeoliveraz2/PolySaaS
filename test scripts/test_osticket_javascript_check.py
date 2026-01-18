"""
Check if OSTicket has client-side JavaScript validation that might be blocking login
"""
import os
import sys
import django
import requests
from bs4 import BeautifulSoup
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
django.setup()

from dose.osticket_admin import get_osticket_session

OSTICKET_LOGIN_URL = "https://oliverenterprises.app.saasify.cloud/scp/login.php"

def check_javascript_validation():
    """Fetch login page and check for JavaScript validation"""
    print("="*80)
    print("CHECKING FOR CLIENT-SIDE JAVASCRIPT VALIDATION")
    print("="*80)

    session = get_osticket_session()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }

    response = session.get(OSTICKET_LOGIN_URL, headers=headers, timeout=15, verify=False, allow_redirects=False)

    print(f"\n[STEP 1] Fetched login page")
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all script tags
    scripts = soup.find_all('script')
    print(f"\n[STEP 2] Found {len(scripts)} script tags")

    # Check for form validation
    form = soup.find('form')
    if form:
        print(f"\n[STEP 3] Form found")
        print(f"Form action: {form.get('action', 'NONE')}")
        print(f"Form method: {form.get('method', 'NONE')}")
        print(f"Form onsubmit: {form.get('onsubmit', 'NONE')}")
        print(f"Form id: {form.get('id', 'NONE')}")
        print(f"Form class: {form.get('class', 'NONE')}")

    # Check for JavaScript that might validate the form
    print(f"\n[STEP 4] Checking for JavaScript validation patterns...")

    validation_patterns = [
        r'onsubmit\s*[:=]\s*["\']?function',
        r'addEventListener\s*\(\s*["\']submit["\']',
        r'\.submit\s*\([^)]*function',
        r'validateForm',
        r'checkForm',
        r'validateCSRF',
        r'csrf',
        r'OSTSESSID',
        r'access.*denied',
        r'Access.*Denied',
    ]

    all_js = ''
    for script in scripts:
        if script.string:
            all_js += script.string + '\n'

    # Also check inline event handlers
    for tag in soup.find_all(True):
        for attr in ['onclick', 'onsubmit', 'onchange', 'onload']:
            if tag.get(attr):
                all_js += f"{attr}: {tag.get(attr)}\n"

    print(f"Total JavaScript code length: {len(all_js)} characters")

    found_validation = []
    for pattern in validation_patterns:
        matches = re.finditer(pattern, all_js, re.IGNORECASE)
        for match in matches:
            # Get context around the match
            start = max(0, match.start() - 100)
            end = min(len(all_js), match.end() + 100)
            context = all_js[start:end]
            found_validation.append({
                'pattern': pattern,
                'context': context
            })
            print(f"\n[FOUND] Pattern: {pattern}")
            print(f"Context: ...{context}...")

    # Check for specific form submission handlers
    print(f"\n[STEP 5] Checking form submission handlers...")

    # Look for jQuery submit handlers
    jquery_submit = re.search(r'\$\([^)]*\)\.submit\s*\(', all_js, re.IGNORECASE)
    if jquery_submit:
        print(f"Found jQuery submit handler")
        start = max(0, jquery_submit.start() - 200)
        end = min(len(all_js), jquery_submit.end() + 500)
        print(f"Code: ...{all_js[start:end]}...")

    # Look for preventDefault or return false
    prevent_default = re.search(r'preventDefault|return\s+false', all_js, re.IGNORECASE)
    if prevent_default:
        print(f"Found preventDefault or return false")
        start = max(0, prevent_default.start() - 200)
        end = min(len(all_js), prevent_default.end() + 200)
        print(f"Code: ...{all_js[start:end]}...")

    # Check for cookie validation
    cookie_check = re.search(r'cookie|document\.cookie|getCookie', all_js, re.IGNORECASE)
    if cookie_check:
        print(f"\n[FOUND] Cookie-related code")
        start = max(0, cookie_check.start() - 200)
        end = min(len(all_js), cookie_check.end() + 500)
        print(f"Code: ...{all_js[start:end]}...")

    # Save full HTML for inspection
    with open('osticket_login_page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print(f"\n[SAVED] Full HTML saved to osticket_login_page.html")

    # Save all JavaScript
    with open('osticket_javascript.js', 'w', encoding='utf-8') as f:
        f.write(all_js)
    print(f"[SAVED] All JavaScript saved to osticket_javascript.js")

    return found_validation

if __name__ == '__main__':
    check_javascript_validation()

