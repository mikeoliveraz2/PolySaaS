#!/usr/bin/env python3
"""
Create a cleaned version of the external HTML that removes JSF loading dependencies
"""

from bs4 import BeautifulSoup

def clean_html():
    """Remove problematic JSF loading elements from the mapped HTML"""
    
    # Read the mapped HTML
    with open('test_external_mapped.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Remove loading-related elements
    elements_to_remove = [
        {'id': 'cockpit_reloading'},           # Main loading div
        {'id': 'reloadMessage'},               # "Loading" message
        {'id': 'ScriptStoreStatusDialog'},     # "Getting Scripts..." dialog
        {'id': 'loginpasswordLoadingDialog'},  # Login loading dialog
    ]
    
    removed_count = 0
    for selector in elements_to_remove:
        elements = soup.find_all(attrs=selector)
        for element in elements:
            element.decompose()
            removed_count += 1
    
    # Remove problematic scripts that wait for JSF resources
    problem_scripts = soup.find_all('script', string=lambda text: text and ('PrimeFaces' in text or 'adjustLoadingPage' in text))
    for script in problem_scripts:
        script.decompose()
        removed_count += 1
    
    # Remove JSF resource links/scripts that return 404
    jsf_resources = soup.find_all(['link', 'script'], attrs={'href': lambda x: x and 'javax.faces.resource' in x, 'src': lambda x: x and 'javax.faces.resource' in x})
    for resource in jsf_resources:
        resource.decompose()
        removed_count += 1
    
    print(f"Removed {removed_count} problematic elements")
    
    # Add a simple status indicator
    body = soup.find('body')
    if body:
        status_div = soup.new_tag('div', style='position: fixed; top: 10px; right: 10px; background: green; color: white; padding: 10px; z-index: 9999;')
        status_div.string = '✅ Static File Loaded Successfully'
        body.insert(0, status_div)
    
    # Save cleaned version
    with open('test_external_cleaned.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print("Cleaned HTML saved to test_external_cleaned.html")
    print("This version should load without getting stuck on 'Loading...'")

if __name__ == "__main__":
    clean_html()