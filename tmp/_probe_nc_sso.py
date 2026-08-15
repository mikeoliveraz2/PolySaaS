"""Probe pso17 Nextcloud creds and live login (no password print)."""
import json
import os

import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection

BASE = "http://127.0.0.1:8888"

with connection.cursor() as c:
    c.execute("SET search_path TO pso17, public")
    c.execute("SELECT extra_config FROM dose_tenantapp WHERE app_name=%s", ["nextcloud"])
    row = c.fetchone()

cfg = {}
if row and row[0]:
    cfg = row[0]
    if isinstance(cfg, str):
        cfg = json.loads(cfg)

login = cfg.get("nc_login") or cfg.get("nextcloud_login")
password = cfg.get("nc_password") or cfg.get("nextcloud_password")
print("nc_url:", cfg.get("nc_url"))
print("nc_login:", repr(login))
print("password_set:", bool(password), "len:", len(password or ""))
print("keys:", sorted(cfg.keys()) if isinstance(cfg, dict) else type(cfg))

# Does NC have pso17 / spo17?
for user in ("pso17", "spo17", "admin"):
    r = requests.get(
        f"{BASE}/ocs/v2.php/cloud/users/{user}",
        auth=("admin", "admin"),
        headers={"OCS-APIRequest": "true", "Accept": "application/json"},
        timeout=15,
    )
    print(f"ocs user {user}:", r.status_code, (r.text or "")[:120].replace("\n", " "))

if login and password:
    s = requests.Session()
    r1 = s.get(f"{BASE}/login", timeout=15)
    print("GET /login", r1.status_code, "cookies", list(s.cookies.keys()))
    token = None
    if 'data-requesttoken="' in r1.text:
        token = r1.text.split('data-requesttoken="', 1)[1].split('"', 1)[0]
    print("requesttoken:", bool(token), "len", len(token or ""))
    r2 = s.post(
        f"{BASE}/login",
        data={"user": login, "password": password, "requesttoken": token or "", "timezone": "UTC", "timezone_offset": "0"},
        headers={"OCS-APIRequest": "true"},
        timeout=15,
        allow_redirects=False,
    )
    loc = r2.headers.get("Location", "")
    print("POST /login", r2.status_code, "loc", loc[:80], "set-cookie", "Set-Cookie" in r2.headers)
    probe = s.get(
        f"{BASE}/ocs/v2.php/cloud/user",
        headers={"OCS-APIRequest": "true", "Accept": "application/json"},
        timeout=15,
    )
    print("OCS /cloud/user after login", probe.status_code, (probe.text or "")[:160].replace("\n", " "))
