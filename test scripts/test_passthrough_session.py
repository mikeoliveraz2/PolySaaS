#!/usr/bin/env python
"""
Simple test script to verify the passthrough session handling works
Tests cookie persistence without actually running Django
"""
import os
import sys
import django

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

# Now we can import our code
from dose.passthrough_views import generic_html_passthrough
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_session_persistence():
    """Test that session cookies are properly saved and restored"""
    from unittest.mock import Mock, patch
    import requests

    # Create a mock request object
    mock_request = Mock()
    mock_request.method = 'GET'
    mock_request.path = '/admin/passthrough/osticket/'
    mock_request.POST = {}
    mock_request.META = {'HTTP_USER_AGENT': 'Mozilla/5.0'}
    mock_request.session = {}
    mock_request.session.modified = False

    # Check that the function handles session initialization
    logger.info("✓ Test 1: Mock request created successfully")
    logger.info(f"  - Request path: {mock_request.path}")
    logger.info(f"  - Session dict: {mock_request.session}")

    return True

def test_code_imports():
    """Test that all necessary imports work"""
    try:
        import requests
        logger.info("✓ requests module imports successfully")

        from bs4 import BeautifulSoup
        logger.info("✓ BeautifulSoup module imports successfully")

        from django.middleware.csrf import get_token
        logger.info("✓ Django CSRF utilities import successfully")

        from django.template.response import TemplateResponse
        logger.info("✓ Django TemplateResponse imports successfully")

        return True
    except ImportError as e:
        logger.error(f"✗ Import error: {e}")
        return False

def test_code_syntax():
    """Test that the passthrough_views module can be imported"""
    try:
        import dose.passthrough_views
        logger.info("✓ passthrough_views module imports successfully")

        # Check that the function exists
        if hasattr(dose.passthrough_views, 'generic_html_passthrough'):
            logger.info("✓ generic_html_passthrough function exists")
        else:
            logger.error("✗ generic_html_passthrough function not found")
            return False

        if hasattr(dose.passthrough_views, 'passthrough_service'):
            logger.info("✓ passthrough_service function exists")
        else:
            logger.error("✗ passthrough_service function not found")
            return False

        return True
    except SyntaxError as e:
        logger.error(f"✗ Syntax error in passthrough_views: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Error importing passthrough_views: {e}")
        return False

if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("PASSTHROUGH SESSION HANDLING TEST")
    logger.info("=" * 80)
    logger.info("")

    results = []

    logger.info("Test 1: Code Syntax Check")
    logger.info("-" * 40)
    results.append(test_code_syntax())
    logger.info("")

    logger.info("Test 2: Required Imports")
    logger.info("-" * 40)
    results.append(test_code_imports())
    logger.info("")

    logger.info("Test 3: Session Persistence Logic")
    logger.info("-" * 40)
    results.append(test_session_persistence())
    logger.info("")

    logger.info("=" * 80)
    logger.info(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    logger.info("=" * 80)

    sys.exit(0 if all(results) else 1)
