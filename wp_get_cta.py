"""Examine the current CTA section structure on the Home page."""
import requests
import re

SITE = "https://azure-nightingale-589250.hostingersite.com"
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

resp = session.get(f"{SITE}/", timeout=15)
html = resp.text

# Find the CTA section — "Get Early Access" and "Stop Managing Tools"
cta_section = re.search(
    r'(Stop Managing Tools.*?</section>)',
    html, re.DOTALL
)
if cta_section:
    section = cta_section.group(1)
    # Extract the key elements
    links = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', section, re.DOTALL)
    print("CTA Section links:")
    for href, text in links:
        clean = re.sub(r'<[^>]+>', '', text).strip()
        print(f"  '{clean}' → {href}")
    
    # Find form elements if any
    forms = re.findall(r'<form[^>]*>(.*?)</form>', section, re.DOTALL)
    if forms:
        print(f"\nForms found: {len(forms)}")
    else:
        print("\nNo forms in CTA section")

# Also check the Sign Up page
print("\n--- Sign Up Page ---")
resp2 = session.get(f"{SITE}/sign-up/", timeout=15)
html2 = resp2.text

forms = re.findall(r'<form[^>]*class="([^"]*)"[^>]*action="([^"]*)"', html2)
print(f"Forms on Sign Up page: {len(forms)}")
for cls, action in forms:
    print(f"  class='{cls}' action='{action}'")

# Check if there's a contact form plugin
inputs = re.findall(r'<input[^>]*name="([^"]*)"[^>]*type="([^"]*)"', html2)
for name, itype in inputs:
    if name not in ('_wp_http_referer', 'wp-submit'):
        print(f"  Input: name='{name}' type='{itype}'")

textareas = re.findall(r'<textarea[^>]*name="([^"]*)"', html2)
for name in textareas:
    print(f"  Textarea: name='{name}'")

# Check for existing form plugins
if 'wpforms' in html2.lower():
    print("\n  WPForms detected")
if 'contact-form-7' in html2.lower() or 'wpcf7' in html2.lower():
    print("\n  Contact Form 7 detected")
if 'gravity' in html2.lower():
    print("\n  Gravity Forms detected")
if 'forminator' in html2.lower():
    print("\n  Forminator detected")
if 'bricks-element-form' in html2.lower() or 'brxe-form' in html2.lower():
    print("\n  Bricks native form detected")
