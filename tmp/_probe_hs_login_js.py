"""Find HubSpot login URL validation in bundles."""
import re
import requests

r = requests.get(
    "https://app.hubspot.com/login/",
    headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"},
    timeout=30,
)
html = r.text
print("status", r.status_code, "len", len(html))
print("invalid in raw html:", "login url is invalid" in html.lower())

scripts = re.findall(r'src="([^"]+\.js[^"]*)"', html)
print("script count", len(scripts))
for s in scripts[:10]:
    print(" ", s[:140])

# fetch first few hsappstatic bundles and search
for s in scripts[:8]:
    if not s.startswith("http"):
        continue
    try:
        js = requests.get(s, timeout=20, headers={"Accept-Encoding": "identity"}).text
    except Exception as exc:
        print("fail", s[:80], exc)
        continue
    low = js.lower()
    if "login url is invalid" in low or "invalid login url" in low:
        print("FOUND invalid text in", s[:100])
        pos = low.find("login url is invalid")
        if pos < 0:
            pos = low.find("invalid login")
        print(js[max(0, pos - 120) : pos + 180])
