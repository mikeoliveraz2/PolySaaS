"""See if Nextcloud login POST rejects wrong Referer/Origin."""
import re
import requests

BASE = "http://127.0.0.1:8888"

def session_and_token():
    s = requests.Session()
    r1 = s.get(f"{BASE}/login", timeout=10)
    m = re.search(r'data-requesttoken="([^"]+)"', r1.text)
    return s, m.group(1) if m else ""

def post(ref, origin):
    s, rt = session_and_token()
    return s.post(
        f"{BASE}/login",
        data={
            "user": "admin",
            "password": "admin",
            "timezone": "Asia/Singapore",
            "timezone_offset": "8",
            "requesttoken": rt,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": ref,
            "Origin": origin,
        },
        allow_redirects=False,
        timeout=10,
    )

r_ok = post(f"{BASE}/login", BASE)
print("Referer=8888 Origin=8888:", r_ok.status_code, r_ok.headers.get("Location", ""))

r_bad = post("http://localhost:8000/pt/admin/nextcloud/login", "http://localhost:8000")
print("Referer=8000 proxy Origin=8000:", r_bad.status_code, r_bad.headers.get("Location", ""))
