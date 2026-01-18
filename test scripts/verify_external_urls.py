#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

try:
    print("Fetching external OSTicket page...")
    response = requests.get('https://demozone.surpaascompaas.com/surpaas/', timeout=10)
    print(f"Status: {response.status_code}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    print("\n=== CSS Links ===")
    css_links = soup.find_all('link', href=True)
    for i, link in enumerate(css_links[:8]):
        href = link.get('href')
        print(f"{i+1}. {href}")
    
    print("\n=== JavaScript Scripts ===")
    js_scripts = soup.find_all('script', src=True) 
    for i, script in enumerate(js_scripts[:8]):
        src = script.get('src')
        print(f"{i+1}. {src}")
    
    print("\n=== Images ===")
    images = soup.find_all('img', src=True)
    for i, img in enumerate(images[:8]):
        src = img.get('src')
        print(f"{i+1}. {src}")
        
    print("\n=== Sample HTML Structure ===")
    print(str(soup)[:800] + "...")
    
except Exception as e:
    print(f"Error: {e}")