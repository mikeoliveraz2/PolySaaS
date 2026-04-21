"""Find and remove content that appears after the footer on the About Us page.
The Roadmap image/caption is showing below the footer section."""
import requests, json, sys, re
sys.stdout.reconfigure(encoding='utf-8')

AZURE = "https://azure-nightingale-589250.hostingersite.com"
s = requests.Session()
s.auth = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

PAGE_ID = 1345

r = s.get(f"{AZURE}/wp-json/wp/v2/pages/{PAGE_ID}?context=edit", timeout=30)
page = r.json()
content = page['content']['raw']

print(f"Total content length: {len(content)}")

# Find the footer section (the last wp:html block with "Stop Managing Tools")
footer_text = "Stop Managing Tools"
footer_pos = content.rfind(footer_text)
print(f"\nFooter text at position: {footer_pos}")

# Show the last 3000 chars to understand structure
print(f"\n=== LAST 3000 CHARS ===")
print(content[-3000:])
