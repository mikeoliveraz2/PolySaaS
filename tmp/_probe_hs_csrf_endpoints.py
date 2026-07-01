"""Probe HubSpot endpoints that might set csrf.app."""
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Encoding": "identity",
    "Referer": "https://app-na2.hubspot.com/login/",
    "Origin": "https://app-na2.hubspot.com",
}

URLS = [
    "https://app-na2.hubspot.com/login/",
    "https://api.hubspot.com/firealarm/v4/alarm/LoginUI",
    "https://app-na2.hubspot.com/api/cookie-consent/v1/status",
    "https://app.hubspot.com/api/login/v1/login-info",
]


def raw_set_cookies(resp):
    out = []
    rh = getattr(resp.raw, "headers", None)
    if rh is None:
        return out
    if hasattr(rh, "getlist"):
        out.extend(rh.getlist("Set-Cookie"))
    else:
        out.extend(v for k, v in rh.items() if k.lower() == "set-cookie")
    return out


for url in URLS:
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
    except Exception as exc:
        print(url, "ERROR", exc)
        continue
    cookies = raw_set_cookies(r)
    names = [c.split("=", 1)[0] for c in cookies]
    print(f"{r.status_code} {url}")
    print(f"  Set-Cookie: {names or '(none)'}")
    for _c in r.cookies:
        if "csrf" in _c.name.lower() or "hubspot" in _c.name.lower():
            print(f"  jar: {_c.name}")
