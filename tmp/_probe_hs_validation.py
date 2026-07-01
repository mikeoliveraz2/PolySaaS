"""Find HubSpot login URL validation source."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

r = requests.get(
    "https://app-na2.hubspot.com/login/",
    headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"},
    timeout=30,
)
html = r.text
print("final url", r.url)
print("len", len(html))

for pat in (
    "login URL is invalid",
    "login url is invalid",
    "invalidLogin",
    "INVALID_LOGIN",
    "loginUrl",
    "isValidLogin",
    "magicLink",
    "window.location",
    "document.URL",
    "document.baseURI",
):
    c = html.count(pat) if pat[0].isupper() or pat.startswith("login") else html.lower().count(pat.lower())
    if c:
        print(f"  {pat!r}: {c}")

# inline scripts snippets
for m in re.finditer(r"<script[^>]*>(.{0,200})", html, re.I | re.S):
    chunk = m.group(1).replace("\n", " ")[:180]
    if "login" in chunk.lower() or "location" in chunk.lower():
        print("INLINE:", chunk[:160])

scripts = re.findall(r'src="([^"]+)"', html)
scripts += re.findall(r"src='([^']+)'", html)
js = [s for s in scripts if ".js" in s or "loginui" in s.lower() or "hsappstatic" in s]
print("js-like", len(js))
for s in js[:30]:
    print(" ", s[:150])

needles = (
    "login url is invalid",
    "loginURL is invalid",
    "invalid login",
    "pathname",
    "document.URL",
    "baseURI",
)
for url in js[:25]:
    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = "https://app-na2.hubspot.com" + url
    if not url.startswith("http"):
        continue
    try:
        js = requests.get(url, timeout=25, headers={"Accept-Encoding": "identity"}).text
    except Exception as exc:
        print("fail", url[:80], exc)
        continue
    low = js.lower()
    hits = [n for n in needles if n.lower() in low]
    if hits:
        print("HIT", url[:100], hits)
        pos = low.find("login url is invalid")
        if pos < 0:
            for n in needles:
                pos = low.find(n.lower())
                if pos >= 0:
                    break
        if pos >= 0:
            print("  ...", js[max(0, pos - 100) : pos + 160].replace("\n", " ")[:260])
