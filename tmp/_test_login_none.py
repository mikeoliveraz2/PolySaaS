import re
import requests

BASE = "http://127.0.0.1:8000"
s = requests.Session()
r = s.get(BASE + "/accounts/login/", timeout=20)
print("GET /accounts/login/ ->", r.status_code)
next_m = re.search(r'name="next" value="([^"]*)"', r.text)
print("next hidden:", repr(next_m.group(1) if next_m else "NOT FOUND"))
csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text)
if csrf:
    for next_val in ("None", "", "/admin/"):
        s2 = requests.Session()
        g = s2.get(BASE + "/accounts/login/", timeout=20)
        tok = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', g.text).group(1)
        data = {
            "login": "olientAdmin",
            "password": "olientPasswor123!",
            "csrfmiddlewaretoken": tok,
            "next": next_val,
        }
        r2 = s2.post(
            BASE + "/accounts/login/",
            data=data,
            headers={"Referer": BASE + "/accounts/login/"},
            allow_redirects=False,
            timeout=20,
        )
        print(f"POST next={next_val!r} -> {r2.status_code} Location={r2.headers.get('Location')}")

r3 = requests.get(BASE + "/accounts/login/None", timeout=10)
print("GET /accounts/login/None ->", r3.status_code)
