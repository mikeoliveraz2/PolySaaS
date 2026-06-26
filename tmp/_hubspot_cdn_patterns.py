import re
import requests

r = requests.get(
    "https://app-na2.hubspot.com/login",
    headers={"Accept-Encoding": "identity"},
    timeout=30,
)
html = r.text
patterns = [
    (r'src=(["\'])(/static\.hsappstatic\.net[^"\']+)\1', "root-relative /static.hsappstatic"),
    (r'src=(["\'])(//static\.hsappstatic\.net[^"\']+)\1', "protocol-relative //static"),
    (r'href=(["\'])(/static\.hsappstatic\.net[^"\']+)\1', "href root-relative"),
    (r'src=(["\'])(https://static\.hsappstatic\.net[^"\']+)\1', "explicit https"),
]
for pat, label in patterns:
    m = re.findall(pat, html, re.I)
    print(label, len(m))
    for _, x in m[:3]:
        print(" ", x[:110])
