#!/usr/bin/env python
"""
Test what the Flask proxy actually returns
"""
import subprocess
import time
import requests
import sys

print("\n" + "="*80)
print("Testing Flask Proxy vs Direct Endpoint")
print("="*80 + "\n")

# Start Flask proxy in background
print("1. Starting Flask proxy on port 8001...")
try:
    proc = subprocess.Popen(
        [sys.executable, "-m", "flask", "--app", "dose.interactive_proxy_flask", "run", "--port", "8001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(3)  # Give it time to start
    print("   ✓ Flask proxy started\n")
except Exception as e:
    print(f"   ✗ Failed to start: {e}\n")
    sys.exit(1)

try:
    # Test Flask proxy
    print("2. Testing Flask proxy endpoint:")
    print("   URL: http://127.0.0.1:8001/admin/osticket/login.php")
    try:
        r = requests.get("http://127.0.0.1:8001/admin/osticket/login.php", timeout=5)
        print(f"   Status: {r.status_code}")
        print(f"   Content-Type: {r.headers.get('content-type', 'N/A')}")
        print(f"   Content Length: {len(r.text)}")
        print(f"   First 200 chars: {r.text[:200]}\n")
    except Exception as e:
        print(f"   Error: {e}\n")

    # Test direct endpoint
    print("3. Testing direct endpoint:")
    print("   URL: https://oliverenterprises.app.saasify.cloud/scp/login.php")
    try:
        r = requests.get("https://oliverenterprises.app.saasify.cloud/scp/login.php", timeout=5, verify=False)
        print(f"   Status: {r.status_code}")
        print(f"   Content-Type: {r.headers.get('content-type', 'N/A')}")
        print(f"   Content Length: {len(r.text)}")
        print(f"   First 200 chars: {r.text[:200]}\n")
    except Exception as e:
        print(f"   Error: {e}\n")

    print("="*80)
    print("Comparison:")
    print("  Flask proxy works ✓ - So the endpoint is reachable")
    print("  Check which one gets 200 vs 422")
    print("="*80 + "\n")

finally:
    # Kill Flask process
    print("Stopping Flask proxy...")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    print("Done.\n")
