"""Fix Sign Up page dark mode - text invisible, form fields white on dark."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/1399",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# Show current content around the heading and form
print(f"Content length: {len(content)}")
print(f"\nFirst 2000 chars:\n{content[:2000]}")
