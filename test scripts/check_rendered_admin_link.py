#!/usr/bin/env python
"""
Check the actual rendered HTML of the Admin link in dashboard
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from bs4 import BeautifulSoup

User = get_user_model()

print("\n" + "="*60)
print("RENDERED HTML DIAGNOSTIC")
print("="*60)

# Get staff user
user = User.objects.filter(is_staff=True).first()
if not user:
    print("[ERROR] No staff user found")
    exit(1)

print(f"\n[OK] Using user: {user.username}")

# Create client and login
client = Client()
client.force_login(user)

# Get dashboard page
print("\nFetching /dose/dashboard/...")
response = client.get('/dose/dashboard/')

if response.status_code != 200:
    print(f"[ERROR] Dashboard returned status {response.status_code}")
    exit(1)

print(f"[OK] Dashboard loaded successfully (status 200)")

# Parse HTML
html = response.content.decode('utf-8')
soup = BeautifulSoup(html, 'html.parser')

# Find navigation links
print("\n" + "="*60)
print("NAVIGATION LINKS IN DASHBOARD:")
print("="*60)

nav_div = soup.find('div', class_='nav')
if nav_div:
    links = nav_div.find_all('a')
    for i, link in enumerate(links, 1):
        href = link.get('href', 'NO HREF')
        text = link.get_text(strip=True)
        onclick = link.get('onclick', '')
        target = link.get('target', '')

        print(f"\n{i}. {text}")
        print(f"   href: {href}")
        if onclick:
            print(f"   onclick: {onclick}")
        if target:
            print(f"   target: {target}")

        # Special check for Admin link
        if 'Admin' in text:
            print(f"   [ADMIN LINK FOUND]")
            print(f"   Full HTML: {link}")
else:
    print("[ERROR] Navigation div not found")

# Check if there's any JavaScript that might affect navigation
print("\n" + "="*60)
print("CHECKING FOR NAVIGATION JAVASCRIPT:")
print("="*60)

scripts = soup.find_all('script')
nav_related_scripts = []

for script in scripts:
    script_text = script.string or ''
    if any(keyword in script_text.lower() for keyword in ['href', 'click', 'navigate', 'location', 'router']):
        nav_related_scripts.append(script_text[:200] + '...' if len(script_text) > 200 else script_text)

if nav_related_scripts:
    print(f"[INFO] Found {len(nav_related_scripts)} script(s) that mention navigation-related keywords")
    for i, script in enumerate(nav_related_scripts[:3], 1):  # Show first 3
        print(f"\nScript {i}:")
        print(script)
else:
    print("[OK] No suspicious navigation scripts found")

print("\n" + "="*60)
print("DIAGNOSTIC COMPLETE")
print("="*60)
print("\nNEXT STEPS:")
print("1. If href='/admin/' is correct, check browser console")
print("2. Check browser Network tab when clicking Admin")
print("3. Try right-click → Open in new tab on Admin link")
