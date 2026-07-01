"""Probe HubSpot login redirect chain for csrf.app Set-Cookie headers."""
import requests

URLS = [
    "https://app.hubspot.com/login/",
    "https://app-na2.hubspot.com/login/",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",
}


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


def scan(label, resp):
    print(f"\n=== {label} ===")
    print(f"final: {resp.status_code} {resp.url}")
    hops = list(getattr(resp, "history", None) or [])
    print(f"redirect hops: {len(hops)}")
    found = []
    for i, hop in enumerate(hops):
        for sc in raw_set_cookies(hop):
            name = sc.split("=", 1)[0]
            print(f"  hop[{i}] Set-Cookie: {name}")
            if name == "csrf.app" or "csrf" in name.lower():
                found.append(("hop", i, sc[:120]))
    for sc in raw_set_cookies(resp):
        name = sc.split("=", 1)[0]
        print(f"  final Set-Cookie: {name}")
        if name == "csrf.app" or "csrf" in name.lower():
            found.append(("final", -1, sc[:120]))
    for _c in resp.cookies:
        if "csrf" in _c.name.lower():
            print(f"  jar cookie: {_c.name}={_c.value[:24]}...")
            found.append(("jar", -1, _c.name))
    if not found:
        print("  NO csrf* cookies in chain")
    return found


for url in URLS:
    r = requests.get(url, headers=HEADERS, allow_redirects=True, timeout=30)
    scan(url, r)
