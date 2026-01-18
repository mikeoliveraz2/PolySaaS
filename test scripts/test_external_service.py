#!/usr/bin/env python
"""
Quick test to check what's happening with the external service
"""
import requests
import sys

def test_external_service():
    print("Testing external service directly...")
    
    # Test URLs
    test_urls = [
        "https://demozone.surpaascompaas.com/surpaas/",
        "https://demozone.surpaascompaas.com/surpaas/surpaas/",
        "https://demozone.surpaascompaas.com/",
    ]
    
    for url in test_urls:
        print(f"\n--- Testing: {url} ---")
        try:
            response = requests.get(url, timeout=10, allow_redirects=False)
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"Content-Length: {len(response.content)} bytes")
            print(f"Headers: {dict(response.headers)}")
            
            if len(response.content) > 0:
                content_preview = response.content[:200].decode('utf-8', errors='ignore')
                print(f"Content preview: {repr(content_preview)}")
            else:
                print("EMPTY CONTENT - This would cause endless loading!")
                
        except requests.exceptions.Timeout:
            print("TIMEOUT - External service not responding")
        except requests.exceptions.ConnectionError:
            print("CONNECTION ERROR - Cannot reach external service")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    test_external_service()