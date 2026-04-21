"""Fix nav menu colors: dark mode current=white others=blue, light mode current=blue others=black."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

# Check the homepage for existing nav CSS rules
r = requests.get(BASE + "/wp-json/wp/v2/pages/1313",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# Find all existing nav-related CSS
for m in re.finditer(r'(?:header-navigation|current-menu-item|\.menu > li)[^}]*\}', content):
    start = max(0, m.start() - 80)
    print(f"--- at {m.start()} ---")
    print(content[start:m.end()])
    print()
