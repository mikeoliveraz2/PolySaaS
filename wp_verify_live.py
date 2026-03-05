"""Verify that the published CSS is being served on rendered pages."""
import requests
import re

SITE = "https://azure-nightingale-589250.hostingersite.com"

pages = [
    ('Home', '/'),
    ('Architecture', '/architecture/'),
    ('Odoo', '/odoo/'),
    ('About Us', '/about-us/'),
]

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

for name, slug in pages:
    url = f"{SITE}{slug}"
    resp = session.get(url, timeout=15)
    html = resp.text

    has_our_css = 'PolySaaS Site-Wide Brand Uniformity' in html
    has_brxe_override = '#brxe-lxtgtl' in html and '#003399' in html

    # Check for a <style> block containing our CSS
    style_blocks = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
    found_in_style = False
    for block in style_blocks:
        if '#brxe-9d3229' in block and 'background-image: none' in block:
            found_in_style = True
            break

    # Check if the old off-brand color is still in Bricks' own styles
    has_old_mint = False
    for block in style_blocks:
        if '#6bff9f' in block:
            has_old_mint = True
            break

    print(f"[{name}]")
    print(f"  Our CSS comment in HTML:    {'YES' if has_our_css else 'NO'}")
    print(f"  Our overrides in <style>:   {'YES' if found_in_style else 'NO'}")
    print(f"  Architecture CTA override:  {'YES' if has_brxe_override else 'NO'}")
    print(f"  Old #6bff9f still present:  {'YES (Bricks original)' if has_old_mint else 'NO'}")
    print()
