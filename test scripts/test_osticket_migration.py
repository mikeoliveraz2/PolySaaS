#!/usr/bin/env python
"""Test suite for osticket package migration."""

import sys

print("=" * 60)
print("OSTICKET PACKAGE MIGRATION TEST")
print("=" * 60)

# Test 1: Package imports
try:
    from dose.osticket import app, run
    print("✓ Test 1: dose.osticket imports successful")
except Exception as e:
    print(f"✗ Test 1 FAILED: {e}")
    sys.exit(1)

# Test 2: Flask app exists and is configured
try:
    assert app is not None
    assert app.name == 'dose.osticket.proxy'
    print("✓ Test 2: Flask app configured correctly")
except Exception as e:
    print(f"✗ Test 2 FAILED: {e}")
    sys.exit(1)

# Test 3: Routes are registered
try:
    routes = [str(rule) for rule in app.url_map.iter_rules()]
    assert '/admin/osticket/' in routes
    assert '/admin/osticket/<path:path>' in routes
    print("✓ Test 3: Proxy routes registered")
except Exception as e:
    print(f"✗ Test 3 FAILED: {e}")
    sys.exit(1)

# Test 4: Screen scraper can import
try:
    from dose.screen_scraper_testor import interactive_repl
    print("✓ Test 4: Screen scraper REPL imports successfully")
except Exception as e:
    print(f"✗ Test 4 FAILED: {e}")
    sys.exit(1)

# Test 5: Proxy functions are available
try:
    from dose.osticket.proxy import doseify_html, _session_store
    assert callable(doseify_html)
    assert isinstance(_session_store, dict)
    print("✓ Test 5: Proxy utility functions available")
except Exception as e:
    print(f"✗ Test 5 FAILED: {e}")
    sys.exit(1)

# Test 6: __main__ module can be run
try:
    from dose.osticket import __main__
    print("✓ Test 6: __main__.py entry point available")
except Exception as e:
    print(f"✗ Test 6 FAILED: {e}")
    sys.exit(1)

print("=" * 60)
print("ALL TESTS PASSED ✓")
print("=" * 60)
print("\nPackage is ready to use:")
print("  • python -m dose.osticket  (to start server)")
print("  • from dose.osticket import app, run")
