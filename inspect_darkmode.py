"""
Inspect the current dark mode CSS on the homepage to find what's broken.
"""
import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Get rendered page
r = s.get(f"{AZURE}")
html = r.text

# Extract all style blocks
styles = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
print(f"Found {len(styles)} style blocks total")

for i, style in enumerate(styles):
    if 'dark-mode' in style or 'ps-' in style:
        print(f"\n{'='*60}")
        print(f"Style block #{i} ({len(style)} chars)")
        print(f"{'='*60}")
        # Print the full dark mode section
        print(style[:10000])
        if len(style) > 10000:
            print(f"\n... (truncated, {len(style)} total chars)")

print("\n\nDone!")
