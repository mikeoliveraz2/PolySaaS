"""Apply Nextcloud sniff HTML rewrite to a logged-in /apps/files/ page and show CSS hrefs."""
import os
import re
import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection
from dose.passthrough.handlers.nextcloud_handler import NextcloudPassthroughHandler

BASE = "http://127.0.0.1:8888"

with connection.cursor() as c:
    c.execute("SET search_path TO pso17, public")
    c.execute(
        "SELECT extra_config FROM dose_tenantapp WHERE extra_config::text ILIKE %s LIMIT 5",
        ["%nc_login%"],
    )
    rows = c.fetchall()

import json
login = password = None
for (cfg,) in rows:
    if isinstance(cfg, str):
        cfg = json.loads(cfg)
    if isinstance(cfg, dict) and cfg.get("nc_login") and cfg.get("nc_password"):
        login, password = cfg["nc_login"], cfg["nc_password"]
        break

s = requests.Session()
r1 = s.get(f"{BASE}/login", timeout=15)
tok = r1.text.split('data-requesttoken="', 1)[1].split('"', 1)[0]
s.post(
    f"{BASE}/login",
    data={"user": login, "password": password, "requesttoken": tok, "timezone": "UTC", "timezone_offset": "0"},
    headers={"requesttoken": tok},
    timeout=15,
    allow_redirects=True,
)
html = s.get(f"{BASE}/apps/files/", timeout=15).text

class _Req:
    _polysniffer_proxy_prefix = "/pt/polysniff/3"
    _passthrough_endpoint = None

h = NextcloudPassthroughHandler()
rewritten, _ = h.process_html_response(
    html,
    request=_Req(),
    endpoint_url="http://localhost:8888",
)

def css_hrefs(blob):
    return re.findall(r'href=["\']([^"\']+\.css[^"\']*)["\']', blob, re.I)

print("ORIGINAL css sample:")
for u in css_hrefs(html)[:8]:
    print(" ", u)
print("REWRITTEN css sample:")
for u in css_hrefs(rewritten)[:8]:
    print(" ", u)
print("rewritten has /pt/polysniff", "/pt/polysniff" in rewritten)
print("rewritten has /pt/admin", "/pt/admin/" in rewritten)
print("rewritten has shim", "data-polysaas-nc-shim" in rewritten)
print("request is None prefix path", "/pt/admin/localhost:8888/core/css/server.css" in rewritten)
