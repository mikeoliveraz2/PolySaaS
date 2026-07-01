import re
import requests

BASE = "http://127.0.0.1:8000"
s = requests.Session()
r = s.get(BASE + "/accounts/login/?next=/admin/", timeout=30)
token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', r.text).group(1)

for label, data in [
    ("empty_password", {"login": "olientAdmin", "password": "", "csrfmiddlewaretoken": token, "next": "/admin/"}),
    ("no_password_key", {"login": "olientAdmin", "csrfmiddlewaretoken": token, "next": "/admin/"}),
    ("correct", {"login": "olientAdmin", "password": "olientPasswor123!", "csrfmiddlewaretoken": token, "next": "/admin/"}),
]:
    s2 = requests.Session()
    g = s2.get(BASE + "/accounts/login/", timeout=30)
    tok = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', g.text).group(1)
    data["csrfmiddlewaretoken"] = tok
    r2 = s2.post(BASE + "/accounts/login/", data=data, headers={"Referer": BASE + "/accounts/login/"}, allow_redirects=False, timeout=30)
    invalid = "invalid username or password" in r2.text.lower()
    print(label, "status", r2.status_code, "redirect", r2.headers.get("Location"), "invalid_msg", invalid)
