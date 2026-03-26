"""Get context around the PolySaaS logo image."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

logo_pos = content.find('Industrial-PolySaas-Cropped-300-Transparent.png" alt="PolySaaS Logo"')
print(f"Logo position: {logo_pos}")
if logo_pos > 0:
    start = max(0, logo_pos - 500)
    end = min(len(content), logo_pos + 500)
    print("=== Context around logo ===")
    print(content[start:end])
