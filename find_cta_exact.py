"""Find the exact structure around LinkedIn link on investor page."""
import requests, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://polysaas.online"
AUTH = ("mikeoliveraz@gmail.com", "vlop MpGU Os2V xDSI C6T7 2fAN")

r = requests.get(BASE + "/wp-json/wp/v2/pages/2565",
                 params={"context": "edit", "_fields": "content"},
                 auth=AUTH, timeout=45)
content = r.json()["content"]["raw"]

# Find LinkedIn in HTML (not CSS)
pos = content.find('linkedin.com/in/')
if pos > 0:
    start = max(0, pos - 100)
    end = min(len(content), pos + 300)
    print(f"LinkedIn link at {pos}:")
    print(repr(content[start:end]))
