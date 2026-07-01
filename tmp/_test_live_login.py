import re
import sys

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
USER = sys.argv[2] if len(sys.argv) > 2 else "olientAdmin"
PWD = sys.argv[3] if len(sys.argv) > 3 else "olientPasswor123!"

s = requests.Session()
r = s.get(f"{BASE}/accounts/login/", timeout=20)
print("GET", r.status_code, "len", len(r.text))
m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
token = m.group(1) if m else None
print("csrf_in_html", bool(token))
if not token:
    token = s.cookies.get("csrftoken")
    print("csrf_cookie", bool(token))
r2 = s.post(
    f"{BASE}/accounts/login/",
    data={
        "login": USER,
        "password": PWD,
        "csrfmiddlewaretoken": token or "",
    },
    headers={"Referer": f"{BASE}/accounts/login/"},
    allow_redirects=False,
    timeout=20,
)
print("POST", r2.status_code, "Location", r2.headers.get("Location"))
body = r2.text.lower()
print("has_invalid_msg", "invalid username or password" in body)
print("sessionid", bool(s.cookies.get("sessionid")))
