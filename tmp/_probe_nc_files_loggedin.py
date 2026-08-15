"""Login as provisioned NC user and inspect /apps/files/ HTML (no secrets printed)."""
import os
import re
import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.db import connection

BASE = "http://127.0.0.1:8888"

with connection.cursor() as c:
    c.execute("SET search_path TO pso17, public")
    c.execute(
        "SELECT id, extra_config FROM dose_tenantapp WHERE extra_config::text ILIKE %s LIMIT 5",
        ["%nc_login%"],
    )
    rows = c.fetchall()

login = None
password = None
for _id, cfg in rows:
    if isinstance(cfg, str):
        import json
        cfg = json.loads(cfg)
    if isinstance(cfg, dict) and cfg.get("nc_login") and cfg.get("nc_password"):
        login = cfg["nc_login"]
        password = cfg["nc_password"]
        print("found extra_config user", login, "tenantapp", _id)
        break

if not login:
    print("NO nc_login in tenantapp extra_config")
    raise SystemExit(1)

s = requests.Session()
r1 = s.get(f"{BASE}/login", timeout=15)
print("GET /login", r1.status_code, "len", len(r1.text), "skip", "Skip to main content" in r1.text)
print("login has confirm password", "confirm your password" in r1.text.lower())
print("login base", re.findall(r"<base[^>]*>", r1.text, re.I)[:3])
links = re.findall(r"<(?:link|script)[^>]*(?:href|src)=[\"']([^\"']+)[\"']", r1.text, re.I)
print("login assets", len(links))
for u in links[:15]:
    print(" ", u[:140])

tok = ""
if 'data-requesttoken="' in r1.text:
    tok = r1.text.split('data-requesttoken="', 1)[1].split('"', 1)[0]
print("requesttoken present", bool(tok), "len", len(tok))

r2 = s.post(
    f"{BASE}/login",
    data={
        "user": login,
        "password": password,
        "requesttoken": tok,
        "timezone": "UTC",
        "timezone_offset": "0",
    },
    headers={"requesttoken": tok},
    timeout=15,
    allow_redirects=False,
)
print("POST /login", r2.status_code, "loc", (r2.headers.get("Location") or "")[:100])

# follow to files
r3 = s.get(f"{BASE}/apps/files/", timeout=15, allow_redirects=True)
print("GET /apps/files/", r3.status_code, "final", r3.url, "len", len(r3.text), "ct", (r3.headers.get("Content-Type") or "")[:60])
t = r3.text
print("files skip", "Skip to main content" in t)
print("files confirm password", "confirm your password" in t.lower())
print("files vue/files", "files-list" in t or "id=\"content-vue\"" in t or "id=\"app-content\"" in t)
print("files base", re.findall(r"<base[^>]*>", t, re.I)[:3])
links = re.findall(r"<(?:link|script)[^>]*(?:href|src)=[\"']([^\"']+)[\"']", t, re.I)
print("files assets", len(links))
for u in links[:20]:
    print(" ", u[:140])
idx = t.lower().find("confirm your password")
if idx >= 0:
    print("snippet:", re.sub(r"\s+", " ", t[max(0, idx - 100) : idx + 140]))
# title
for m in re.findall(r"<title[^>]*>(.*?)</title>", t, re.I | re.S)[:1]:
    print("title", re.sub(r"\s+", " ", m).strip()[:120])
