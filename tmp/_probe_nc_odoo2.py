"""Check if Nextcloud user ODOO2 exists; print menu URL fields only."""
import os
import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection

BASE = "http://127.0.0.1:8888"

with connection.cursor() as c:
    c.execute("SET search_path TO pso17, public")
    c.execute(
        "SELECT id, slug, endpoint_url, starting_uri, menu_title FROM dose_passthroughendpoint "
        "WHERE slug ILIKE %s OR endpoint_url ILIKE %s",
        ["%nextcloud%", "%8888%"],
    )
    print("endpoints:", c.fetchall())

r = requests.get(
    f"{BASE}/ocs/v2.php/cloud/users/ODOO2",
    auth=("admin", "admin"),
    headers={"OCS-APIRequest": "true", "Accept": "application/json"},
    timeout=15,
)
print("ocs ODOO2 admin/admin:", r.status_code, (r.text or "")[:180].replace("\n", " "))

# Try form login as ODOO2 without printing password
pw = "PlySaaS2026!"
s = requests.Session()
r1 = s.get(f"{BASE}/login", timeout=15)
tok = ""
if 'data-requesttoken="' in r1.text:
    tok = r1.text.split('data-requesttoken="', 1)[1].split('"', 1)[0]
r2 = s.post(
    f"{BASE}/login",
    data={"user": "ODOO2", "password": pw, "requesttoken": tok, "timezone": "UTC", "timezone_offset": "0"},
    headers={"requesttoken": tok, "OCS-APIRequest": "true"},
    timeout=15,
    allow_redirects=False,
)
print("ODOO2 POST /login", r2.status_code, "loc", (r2.headers.get("Location") or "")[:80])
probe = s.get(
    f"{BASE}/ocs/v2.php/cloud/user",
    headers={"OCS-APIRequest": "true", "Accept": "application/json"},
    timeout=15,
)
print("OCS after ODOO2 login", probe.status_code, (probe.text or "")[:200].replace("\n", " "))
