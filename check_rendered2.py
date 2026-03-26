"""Fetch rendered page and check exact HTML around Platform Features."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

r = requests.get("https://azure-nightingale-589250.hostingersite.com/", timeout=30)
html = r.text

pf_pos = html.find('id="platform-features"')
if pf_pos > 0:
    # Show 800 chars before and 200 after
    start = max(0, pf_pos - 800)
    end = min(len(html), pf_pos + 200)
    snippet = html[start:end]
    print(snippet)
else:
    print("Platform Features not found!")
