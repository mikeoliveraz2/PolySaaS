"""Check the rendered HTML around the logo section to find white space sources."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"

r = requests.get(BASE + "/", timeout=30)
html = r.text

# Find the logo bg section
pos = html.find('hero-bg-neural')
if pos > 0:
    start = max(0, pos - 1500)
    end = min(len(html), pos + 800)
    print("=== Rendered HTML around logo bg ===")
    print(html[start:end])
else:
    print("hero-bg-neural not found in rendered HTML")

# Also check body classes and main content wrapper
body_pos = html.find('<body')
if body_pos > 0:
    print("\n=== Body tag ===")
    print(html[body_pos:body_pos+500])

# Find entry-content-wrap
ecw = html.find('entry-content-wrap')
if ecw > 0:
    start2 = max(0, ecw - 100)
    end2 = min(len(html), ecw + 300)
    print("\n=== entry-content-wrap ===")
    print(html[start2:end2])
