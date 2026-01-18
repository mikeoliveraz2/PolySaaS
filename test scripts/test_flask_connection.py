#!/usr/bin/env python
"""Quick test to see if Flask service is running"""
import requests
import sys

try:
    response = requests.get('http://localhost:5000/health', timeout=2)
    print(f"✓ Flask service is running! Status: {response.status_code}")
    print(f"  Response: {response.json()}")
    sys.exit(0)
except requests.exceptions.ConnectionError:
    print("✗ Flask service is NOT running on port 5000")
    print("  Please start it manually:")
    print("  cd pass_through_service")
    print("  python app.py")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error connecting to Flask: {e}")
    sys.exit(1)

