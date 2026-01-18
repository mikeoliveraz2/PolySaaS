#!/usr/bin/env python3
"""
Test URL mapping transformations on static HTML file
"""

from bs4 import BeautifulSoup
from urllib.parse import urlparse

def map_external_urls_to_trigger_path(content, external_base_url, trigger_path):
    """Apply the same URL mapping logic as our middleware"""
    if not external_base_url or not trigger_path:
        return content
    
    # Parse the external URL to get the domain and path
    parsed_external = urlparse(external_base_url)
    external_domain = f"{parsed_external.scheme}://{parsed_external.netloc}"
    external_path = parsed_external.path.rstrip('/')  # e.g., "/surpaas"
    
    print(f"URL mapping: external_domain={external_domain}, external_path={external_path}, trigger_path={trigger_path}")
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Map resources (CSS/JS/images) directly to external server
    # Login screen resources should be publicly accessible
    resources_mapped = 0
    
    # Map CSS files directly to external domain
    for link in soup.find_all('link', href=True):
        href = link['href']
        if href.startswith('/') and not href.startswith('http'):
            # Convert relative URL to absolute external URL (href already includes /surpaas/)
            original_href = href
            link['href'] = f"{external_domain}{href}"
            resources_mapped += 1
            print(f"CSS resource mapped: {original_href} → {link['href']}")
                
    # Map JavaScript files directly to external domain
    for script in soup.find_all('script', src=True):
        src = script['src']
        if src.startswith('/') and not src.startswith('http'):
            # Convert relative URL to absolute external URL (src already includes /surpaas/)
            original_src = src
            script['src'] = f"{external_domain}{src}"
            resources_mapped += 1
            print(f"JS resource mapped: {original_src} → {script['src']}")
                
    # Map image files directly to external domain
    for img in soup.find_all('img', src=True):
        src = img['src']
        if src.startswith('/') and not src.startswith('http'):
            # Convert relative URL to absolute external URL (src already includes /surpaas/)
            original_src = src
            img['src'] = f"{external_domain}{src}"
            resources_mapped += 1
            print(f"Image resource mapped: {original_src} → {img['src']}")
                
    print(f"Mapped {resources_mapped} resources directly to external server")
    
    return str(soup)

def main():
    # Read the external HTML file
    with open('test_external.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply URL mapping
    external_base_url = "https://demozone.surpaascompaas.com/surpaas"
    trigger_path = "/dose/osticket/"
    
    mapped_content = map_external_urls_to_trigger_path(content, external_base_url, trigger_path)
    
    # Save the mapped HTML
    with open('test_external_mapped.html', 'w', encoding='utf-8') as f:
        f.write(mapped_content)
    
    print("\nMapped HTML saved to test_external_mapped.html")
    print("You can now open this file in a browser to test if resources load correctly")

if __name__ == "__main__":
    main()