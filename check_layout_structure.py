"""Check the full layout structure from body to feature blocks."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://azure-nightingale-589250.hostingersite.com"

r = requests.get(BASE, timeout=30)
html = r.text

# Find the Platform Features heading and trace UP the DOM to find all parent containers
pf_pos = html.find('id="platform-features"')
if pf_pos > 0:
    # Get a large chunk before the heading to see parent structure
    start = max(0, pf_pos - 5000)
    chunk = html[start:pf_pos]
    
    # Find all opening div tags with classes
    divs = re.findall(r'<div[^>]*class="([^"]*)"[^>]*(?:style="([^"]*)")?[^>]*>', chunk)
    
    print("=== Parent containers above Platform Features (bottom up) ===")
    # Get last 15 div openings
    for cls, style in divs[-15:]:
        print(f"  class=\"{cls}\"", end="")
        if style:
            print(f" style=\"{style}\"", end="")
        print()

# Also check the page layout class on body
body_match = re.search(r'<body[^>]*class="([^"]*)"[^>]*>', html)
if body_match:
    body_classes = body_match.group(1)
    # Filter relevant classes
    relevant = [c for c in body_classes.split() if any(word in c.lower() for word in ['content', 'layout', 'width', 'boxed', 'full', 'narrow', 'page', 'single'])]
    print(f"\n=== Body layout classes ===")
    print(f"  {' '.join(relevant)}")
    print(f"\n  All body classes: {body_classes[:500]}")

# Check the content container structure
for marker in ['site-container', 'content-container', 'content-area', 'entry-content-wrap', 'site-main']:
    pos = html.find(f'class="{marker}')
    if pos < 0:
        pos = html.find(marker)
    if pos > 0:
        snippet = html[max(0, pos-50):pos+200]
        # Extract just the opening tag
        tag_match = re.search(r'<[a-z]+[^>]*class="[^"]*' + marker + r'[^"]*"[^>]*>', snippet)
        if tag_match:
            print(f"\n  {tag_match.group(0)[:200]}")
