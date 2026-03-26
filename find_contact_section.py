"""Find the contact/CTA section near bottom of investor page."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/2565",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# Search for "15-Minute" or "Quick" or "Call"
for term in ['15-Minute', 'Quick 15', 'Michael Oliver', 'Disclaimer', 'LinkedIn']:
    pos = content.find(term)
    if pos > 0:
        print(f"Found '{term}' at pos {pos}")

# Show last 3000 chars
print(f"\n=== Last 3000 chars ===")
print(content[-3000:])
