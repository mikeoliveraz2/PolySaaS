"""Pinpoint exactly where the old logo still appears in rendered HTML."""
import requests
import re

SITE = "https://azure-nightingale-589250.hostingersite.com"

# Check home page and one inner page to compare
for page_path in ["/", "/architecture/"]:
    r = requests.get(f"{SITE}{page_path}", timeout=20)
    html = r.text
    print(f"=== {page_path} ===\n")

    # Find all occurrences of the old logo pattern with surrounding HTML
    for m in re.finditer(r'Industrial-PolySaas-Cropped-300-Transparent', html):
        start = max(0, m.start() - 300)
        end = min(len(html), m.end() + 200)
        context = html[start:end]
        # Clean up for readability
        context = context.replace('\n', '\n    ')
        print(f"  --- Found at position {m.start()} ---")
        print(f"    {context}")
        print()
    print()
