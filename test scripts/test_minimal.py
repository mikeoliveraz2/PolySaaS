#!/usr/bin/env python
"""Minimal test"""
print("Script started")
import sys
sys.stdout.flush()

try:
    import requests
    print("requests imported")
    sys.stdout.flush()

    r = requests.get("https://httpbin.org/get", timeout=5)
    print(f"HTTP test: {r.status_code}")
    sys.stdout.flush()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.stdout.flush()

print("Script complete")
sys.stdout.flush()

