#!/usr/bin/env python3

"""
Quick script to check what's in the mapped HTML content
"""

import requests
from bs4 import BeautifulSoup

def check_html_content():
    print("Checking HTML content for base URLs and context paths...")
    
    try:
        # Get the content from our Django middleware
        response = requests.get("http://localhost:8000/dose/osticket/", timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for base tags
            base_tags = soup.find_all('base')
            print(f"Found {len(base_tags)} base tags:")
            for base in base_tags:
                print(f"  <base href='{base.get('href', 'N/A')}'>")
            
            # Check for any JavaScript variables that might contain base paths
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    text = script.string
                    if 'contextPath' in text or 'basePath' in text or 'baseUrl' in text:
                        print(f"Found potential base path in script:")
                        print(f"  {text[:200]}...")
            
            # Check form actions
            forms = soup.find_all('form', action=True)
            print(f"Found {len(forms)} forms with actions:")
            for form in forms[:5]:  # Show first 5
                print(f"  <form action='{form['action']}'>")
                
        else:
            print(f"Failed to get content: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_html_content()