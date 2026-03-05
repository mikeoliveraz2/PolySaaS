"""Find body classes on home vs inner pages to target gradient CSS correctly."""
import requests
import re

SITE = "https://azure-nightingale-589250.hostingersite.com"
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

for name, slug in [('Home', '/'), ('Architecture', '/architecture/'), ('Odoo', '/odoo/'), ('Pricing', '/pricing/')]:
    resp = session.get(f"{SITE}{slug}", timeout=15)
    body_match = re.search(r'<body[^>]*class="([^"]*)"', resp.text)
    if body_match:
        classes = body_match.group(1)
        print(f"{name:20s}: {classes[:200]}")
    else:
        print(f"{name:20s}: no body class found")
