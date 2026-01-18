#!/usr/bin/env python
"""
Test OS ticket access and prepare for PolySniffer comparison
This script will help you compare what our proxy sends vs what a real browser sends
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import requests
from bs4 import BeautifulSoup
from dose.osticket_admin import get_osticket_session

# Configuration
OSTICKET_LOGIN_URL = "https://oliverenterprises.app.saasify.cloud/scp/login.php"
OSTICKET_BASE = "https://oliverenterprises.app.saasify.cloud/scp/"

print("="*80)
print("OS Ticket Proxy Test - For PolySniffer Comparison")
print("="*80)
print()
print("This script simulates what our Django proxy does when accessing OS ticket.")
print("Use PolySniffer to capture what a REAL browser does, then compare!")
print()
print("PolySniffer Live Demo: https://polysniffer.up.railway.app")
print()
print("="*80)
print()

# Use persistent session (like our proxy does)
session = get_osticket_session()

print("[STEP 1] GET login page (simulating browser request)")
print("-" * 80)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

try:
    response = session.get(
        OSTICKET_LOGIN_URL,
        headers=headers,
        verify=False,
        timeout=15
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response Headers:")
    for key, value in response.headers.items():
        if key.lower() in ['content-type', 'set-cookie', 'location']:
            print(f"  {key}: {value}")

    print(f"\nCookies in session:")
    for cookie in session.cookies:
        print(f"  {cookie.name}: {cookie.value[:50]}...")

    # Extract CSRF token
    soup = BeautifulSoup(response.text, 'html.parser')
    form = soup.find('form')
    if form:
        csrf_input = form.find('input', {'name': '__CSRFToken__'})
        if csrf_input:
            csrf_token = csrf_input.get('value', '')
            print(f"\nCSRF Token found: {csrf_token[:50]}...")
        else:
            print("\n[WARNING] No CSRF token found in form!")
    else:
        print("\n[WARNING] No form found in response!")

    print(f"\nResponse length: {len(response.text)} bytes")
    print(f"Response preview (first 500 chars):")
    print(response.text[:500])

except Exception as e:
    print(f"[ERROR] Failed to fetch login page: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("Next Steps:")
print("="*80)
print("1. Open PolySniffer: https://polysniffer.up.railway.app")
print("2. Enter OS ticket URL: https://oliverenterprises.app.saasify.cloud/scp/login.php")
print("3. Paste your cookies from browser DevTools (if you have them)")
print("4. Navigate through login flow in PolySniffer")
print("5. Export HAR file from PolySniffer")
print("6. Compare with the output above:")
print("   - Check request headers")
print("   - Check cookies sent")
print("   - Check POST data format")
print("   - Check CSRF token handling")
print("="*80)

