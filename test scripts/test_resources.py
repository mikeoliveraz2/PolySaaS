import requests
import re
import time

def test_resources():
    # Read the mapped HTML file
    with open('test_external_mapped.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract all resource URLs
    css_pattern = r'href="(https://demozone\.surpaascompaas\.com[^"]*\.css[^"]*)"'
    js_pattern = r'src="(https://demozone\.surpaascompaas\.com[^"]*\.js[^"]*)"'
    
    css_urls = re.findall(css_pattern, content)
    js_urls = re.findall(js_pattern, content)
    
    print(f"Found {len(css_urls)} CSS files and {len(js_urls)} JS files")
    
    # Test first 5 CSS files
    print("\n=== Testing CSS Files ===")
    for i, url in enumerate(css_urls[:5]):
        try:
            response = requests.head(url, timeout=10)
            print(f"✅ CSS {i+1}: {response.status_code} - {response.headers.get('content-type', 'unknown')} - {url[:80]}...")
        except Exception as e:
            print(f"❌ CSS {i+1}: ERROR - {str(e)[:50]}... - {url[:80]}...")
    
    # Test first 5 JS files  
    print("\n=== Testing JS Files ===")
    for i, url in enumerate(js_urls[:5]):
        try:
            response = requests.head(url, timeout=10)
            print(f"✅ JS {i+1}: {response.status_code} - {response.headers.get('content-type', 'unknown')} - {url[:80]}...")
        except Exception as e:
            print(f"❌ JS {i+1}: ERROR - {str(e)[:50]}... - {url[:80]}...")

if __name__ == "__main__":
    test_resources()