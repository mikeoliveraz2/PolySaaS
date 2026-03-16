"""Check Kadence theme mods for footer configuration."""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Try to get theme mods via the options endpoint
# Kadence stores footer config in theme_mods_kadence option
r = s.get(f"{AZURE}/wp-json/")
api = r.json()

# Try reading the kadence theme options
# Method 1: Direct options endpoint
for opt_name in ['theme_mods_kadence', 'kadence_global_palette']:
    r = s.post(f"{AZURE}/wp-json/wp/v2/settings", json={})
    # This won't work directly. Let's try a different approach.

# Method 2: Use a custom endpoint if Kadence exposes one  
# Check what endpoints are available
print("Available REST routes (footer/kadence related):")
routes = api.get('routes', {})
for route_path in sorted(routes.keys()):
    if any(kw in route_path.lower() for kw in ['footer', 'kadence', 'widget', 'option', 'setting', 'customiz']):
        print(f"  {route_path}")

# Method 3: Try to get the option directly
print("\n=== Trying to read footer options ===")
# WordPress doesn't expose arbitrary options via REST by default.
# But we can check if any Kadence-specific settings endpoints exist.

# Let's check what the Customizer footer page looks like via browser
# First, let's see the current footer HTML on the rendered page
print("\n=== Checking rendered footer on About Us ===")
r = requests.get(f"{AZURE}/about-us/")
html = r.text

# Find the footer element
import re
footer_match = re.search(r'<footer[^>]*class="site-footer[^"]*"[^>]*>(.*?)</footer>', html, re.DOTALL)
if footer_match:
    footer_html = footer_match.group(0)
    print(f"Site footer found: {len(footer_html)} chars")
    # Check for kadence footer rows
    rows = re.findall(r'class="[^"]*footer-row[^"]*"', footer_html)
    print(f"Footer rows: {rows}")
    widgets = re.findall(r'class="[^"]*footer-widget[^"]*"', footer_html)
    print(f"Footer widgets: {len(widgets)}")
    
    # Show the structure
    # Extract just the class attributes of major divs
    divs = re.findall(r'<div[^>]*class="([^"]*(?:footer|site-bottom)[^"]*)"[^>]*>', footer_html)
    for d in divs:
        print(f"  div class: {d}")
    
    # Show the actual footer content (trimmed)
    print(f"\nFooter HTML (first 500 chars):\n{footer_html[:500]}")
    print(f"\nFooter HTML (last 500 chars):\n...{footer_html[-500:]}")
else:
    print("No <footer class='site-footer'> found!")
    # Try to find any footer element
    footer_tag = re.search(r'<footer[^>]*>(.*?)</footer>', html, re.DOTALL)
    if footer_tag:
        print(f"Found generic footer: {footer_tag.group(0)[:300]}")
    else:
        print("No footer tag at all!")
