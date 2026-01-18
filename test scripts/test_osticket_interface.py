#!/usr/bin/env python
"""
Comprehensive OSTicket Interface Test
Tests the full passthrough flow: menu access → HTML rewriting → form routing
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
import re
import logging

# Suppress verbose logging
logging.getLogger('django').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)

def test_osticket_interface():
    """Full integration test of OSTicket passthrough"""

    logger.info("\n" + "="*100)
    logger.info("OSTICKET INTERFACE COMPREHENSIVE TEST")
    logger.info("="*100 + "\n")

    # 1. Create/get test user
    logger.info("[1/5] Setting up test user...")
    try:
        user = User.objects.get(username='testuser')
        logger.info("     ✓ Test user exists")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            password='test123',
            is_staff=True,
            is_superuser=True
        )
        logger.info("     ✓ Test user created")

    # 2. Log in
    logger.info("\n[2/5] Authenticating user...")
    client = Client()
    login_success = client.login(username='testuser', password='test123')
    if login_success:
        logger.info("     ✓ Authentication successful")
    else:
        logger.error("     ✗ Authentication failed!")
        return False

    # 3. Access OSTicket passthrough
    logger.info("\n[3/5] Accessing /admin/passthrough/osticket/...")
    try:
        response = client.get('/admin/passthrough/osticket/')
        logger.info(f"     ✓ Response received (Status: {response.status_code})")
    except Exception as e:
        logger.error(f"     ✗ Request failed: {e}")
        return False

    # 4. Verify HTML rewriting
    logger.info("\n[4/5] Verifying HTML rewriting...")
    content = response.content.decode('utf-8') if isinstance(response.content, bytes) else response.content

    checks = {
        "Contains login form": '<form' in content,
        "Form action rewritten": '/admin/passthrough/osticket/login.php' in content,
        "CSS links rewritten": '/admin/passthrough/osticket/css/' in content,
        "Image sources rewritten": '/admin/passthrough/osticket/images/' in content or '/admin/passthrough/osticket/logo.php' in content,
        "No double paths": '/scp/login.php/login.php' not in content,
        "No bare domain": 'oliverenterprises.app.saasify.cloud' not in content,
    }

    all_passed = True
    for check_name, result in checks.items():
        status = "✓" if result else "✗"
        logger.info(f"     {status} {check_name}")
        if not result:
            all_passed = False

    # 5. Verify form action details
    logger.info("\n[5/5] Form submission routing verification...")

    # Extract form action
    form_match = re.search(r'<form[^>]*action="([^"]*)"', content)
    if form_match:
        form_action = form_match.group(1)
        logger.info(f"     ✓ Form action: {form_action}")

        # Verify it's the correct proxy path
        if form_action == '/admin/passthrough/osticket/login.php':
            logger.info("     ✓ Form will route to proxy handler (correct!)")
        else:
            logger.error(f"     ✗ Unexpected form action: {form_action}")
            all_passed = False
    else:
        logger.error("     ✗ Could not find form action")
        all_passed = False

    # Final summary
    logger.info("\n" + "="*100)
    if all_passed:
        logger.info("✓✓✓ ALL TESTS PASSED ✓✓✓")
        logger.info("="*100)
        logger.info("\nOSTicket interface is ready for full testing!")
        logger.info("Next steps:")
        logger.info("  1. Access Django admin at http://127.0.0.1:8000/admin/")
        logger.info("  2. Look for OSTicket menu item in top menu")
        logger.info("  3. Click to load the passthrough")
        logger.info("  4. Try entering credentials (will test real OSTicket)")
        logger.info("  5. Navigate through multiple pages")
        return True
    else:
        logger.info("✗✗✗ SOME TESTS FAILED ✗✗✗")
        logger.info("="*100)
        logger.error("\nDebugging needed. Check logs for details.")
        return False

if __name__ == '__main__':
    success = test_osticket_interface()
    sys.exit(0 if success else 1)
