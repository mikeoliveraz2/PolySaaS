"""
Direct HubSpot login API probe — bypasses all PolySaaS proxy machinery.
Run: .\venv\Scripts\python.exe tmp\_test_hs_login_direct.py

Step 1: GET /login/ to see which cookies HubSpot sets server-side.
Step 2: POST with JSON credentials (spoofed Origin/Referer, csrf.app injected).

Fill in EMAIL and PASSWORD before running (or pass as CLI args).
"""
import sys
import requests


EMAIL    = "michael.oliver@polysaas.online"
PASSWORD = input("HubSpot password: ").strip() if len(sys.argv) < 3 else sys.argv[2]
if len(sys.argv) >= 3:
    EMAIL    = sys.argv[1]
    PASSWORD = sys.argv[2]

session = requests.Session()

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Dest": "document",
}

# ─────────────────────────────────────────────────────────
# STEP 1: GET /login/ — see what cookies HubSpot sends us
# ─────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1: GET https://app.hubspot.com/login/")
r_get = session.get(
    "https://app.hubspot.com/login/",
    headers=BROWSER_HEADERS,
    allow_redirects=False,
)
print(f"  Status     : {r_get.status_code}")
print(f"  Location   : {r_get.headers.get('Location', '(none)')}")

# Collect all Set-Cookie headers via urllib3 raw
raw_sc = []
try:
    rh = getattr(r_get.raw, 'headers', None)
    if rh is not None:
        if hasattr(rh, 'getlist'):
            raw_sc = rh.getlist('Set-Cookie')
        elif hasattr(rh, 'items'):
            raw_sc = [v for k, v in rh.items() if k.lower() == 'set-cookie']
except Exception as _e:
    print(f"  [WARN] raw header parse: {_e}")

print(f"  Set-Cookie headers ({len(raw_sc)}):")
for sc in raw_sc:
    print(f"    {sc[:120]}")

# Also show parsed cookies
print(f"  Parsed cookies: {dict(r_get.cookies)}")
csrf_from_get = None
for sc in raw_sc:
    if sc.startswith('csrf.app='):
        csrf_from_get = sc.split(';')[0].split('=', 1)[1].strip()
        break
if csrf_from_get:
    print(f"  *** csrf.app found in GET response: {csrf_from_get[:30]}... ***")
else:
    print("  *** csrf.app NOT in GET response (HubSpot doesn't send it server-side) ***")
print("=" * 60)

# ─────────────────────────────────────────────────────────
# STEP 2: POST /login/ with credentials
# Try A: with csrf.app from GET (if available)
# Try B: with hardcoded csrf.app from browser DevTools
# ─────────────────────────────────────────────────────────

# Hardcoded browser csrf.app — copy fresh from:
# DevTools → Application → Cookies → https://app.hubspot.com → csrf.app
BROWSER_CSRF_APP = "AAccUfvn24e1F1ra-d2esW1F01jjcSiC87BfCRjCwlYJGe8yMkl4yspfJi4N1MoC58Aue0QMd53Srp4fy2MqZ5egIld1skDkzg"

csrf_to_use = csrf_from_get or BROWSER_CSRF_APP
if csrf_to_use == BROWSER_CSRF_APP and not csrf_from_get:
    print(f"[TEST] Using HARDCODED browser csrf.app: {csrf_to_use[:30]}...")
else:
    print(f"[TEST] Using csrf.app from GET response: {csrf_to_use[:30]}...")

session.cookies.set('csrf.app', csrf_to_use, domain='app.hubspot.com', path='/')

payload = {
    "loginPortalId": 0,
    "email": EMAIL,
    "password": PASSWORD,
    "rememberMe": False,
    "otp": "",
    "loginSsoTokenResponse": None,
}

post_headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/html, */*",
    "Origin": "https://app.hubspot.com",
    "Referer": "https://app.hubspot.com/login/",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": BROWSER_HEADERS["User-Agent"],
}

print()
print("=" * 60)
print("STEP 2: POST https://app.hubspot.com/login/  (JSON, allow_redirects=False)")
resp = session.post(
    "https://app.hubspot.com/login/",
    json=payload,
    headers=post_headers,
    allow_redirects=False,
)
print(f"  Status         : {resp.status_code}")
print(f"  Content-Type   : {resp.headers.get('Content-Type', '?')}")
print(f"  Location       : {resp.headers.get('Location', '(none)')}")
print(f"  Set-Cookie keys: {[h[0] for h in resp.headers.items() if h[0].lower()=='set-cookie']}")
ct = resp.headers.get("Content-Type", "")
if "json" in ct:
    print(f"  Body (JSON)    : {resp.text[:500]}")
else:
    print(f"  Body (first 200): {resp.text[:200]!r}")
print("=" * 60)

if resp.status_code in (301, 302, 303, 307, 308):
    print("SUCCESS: HubSpot issued a redirect → login accepted")
elif resp.status_code == 200 and "json" in ct:
    import json as _json
    try:
        j = _json.loads(resp.text)
        if j.get("redirectUrl") or j.get("nextUrl") or j.get("portalId"):
            print("SUCCESS: HubSpot returned JSON with portal/redirect info")
        else:
            print("FAIL: HubSpot returned 200 JSON but no redirect/portal keys")
            print("  Keys:", list(j.keys()))
    except Exception:
        print("FAIL: 200 but body is not valid JSON")
else:
    print("FAIL: HubSpot returned login HTML — credentials rejected or CSRF/Cloudflare blocking")
