import re
import requests

url = "https://app-na2.hubspot.com/login"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
print("status", r.status_code, "len", len(r.text))
html = r.text
for pat in ("hsappstatic", "static/", "src=", "href="):
    print(pat, html.lower().count(pat.lower()))
assets = re.findall(r'(?:src|href)=(["\'])([^"\']+)\1', html)
for _, m in assets[:40]:
    if "static" in m or ".js" in m or ".css" in m or m.startswith("/"):
        print(" ", m[:140])
