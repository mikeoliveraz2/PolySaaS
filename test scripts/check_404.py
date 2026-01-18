#!/usr/bin/env python3
"""
Check what the 404 responses actually contain
"""

import requests

def check_404_responses():
    """Check what the external server returns for 404s"""
    
    test_urls = [
        "https://demozone.surpaascompaas.com/surpaas/javax.faces.resource/jquery/jquery.js.jsf",
        "https://demozone.surpaascompaas.com/surpaas/javax.faces.resource/theme.css.jsf"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            print(f"\n=== {url} ===")
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"Content-Length: {len(response.text)}")
            print(f"Content preview: {response.text[:200]}...")
            
        except Exception as e:
            print(f"Error testing {url}: {e}")

if __name__ == "__main__":
    check_404_responses()