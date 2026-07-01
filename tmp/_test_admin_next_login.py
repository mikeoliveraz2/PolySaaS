import re
import sys

import requests

BASE = "http://localhost:8000"
USER = "olientAdmin"
PWD = "olientPasswor123!"

s = requests.Session()
login_url = f"{BASE}/accounts/login/?next=/admin/"
r = s.get(login_url, timeout=20)
print("GET", r.status_code)
m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
token = m.group(1) if m else s.cookies.get("csrftoken")
has_next_hidden = 'name="next"' in r.text
print("csrf", bool(token), "next_hidden_in_form", has_next_hidden)

r2 = s.post(
    login_url,
    data={
        "login": USER,
        "password": PWD,
        "csrfmiddlewaretoken": token or "",
        "next": "/admin/",
    },
    headers={"Referer": login_url},
    allow_redirects=False,
    timeout=20,
)
print("POST", r2.status_code, "Location", r2.headers.get("Location"))
print("invalid_msg", "invalid username or password" in r2.text.lower())

loc = r2.headers.get("Location") or ""
if loc:
    r3 = s.get(BASE + loc if loc.startswith("/") else loc, allow_redirects=False, timeout=20)
    print("after_login", r3.status_code, "next_loc", r3.headers.get("Location", ""))
