import re
import requests

html = requests.get("https://app-na2.hubspot.com/login", timeout=30).text
for pat in [
    r"<link[^>]+href=(['\"])(//static[^'\"]+)\1",
    r"url\((['\"]?)(//static[^)'\"]+)",
    r'"(//static\.hsappstatic\.net[^"]+)"',
]:
    m = re.findall(pat, html, re.I)
    print(pat[:50], len(m))
    for x in m[:3]:
        print(" ", x)
