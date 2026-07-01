"""Trace MISSING_FRAGMENTS display path in LoginUI."""
import re
import requests

js = requests.get(
    "https://static.hsappstatic.net/LoginUI/static-1.15500/bundles/project.js",
    timeout=30,
    headers={"Accept-Encoding": "identity"},
).text

# Who reads MISSING_FRAGMENTS for display?
for m in re.finditer(r".{0,100}MISSING_FRAGMENTS.{0,150}", js):
    print(m.group(0).replace("\n", " ")[:250])
    print("---")

# Find Ia component (catch-all mobile login)
pos = js.find("isMobileLogin:e})})]})})")
print("\nCatch-all at", pos)
print(js[max(0, pos - 400) : pos + 200].replace("\n", " "))

# Search isMobileLogin
idx = js.find("isMobileLogin")
while idx >= 0 and idx < 500000:
    idx = js.find("isMobileLogin", idx + 1)
    if idx < 0:
        break
print("\nisMobileLogin first at", js.find("isMobileLogin"))
print(js[js.find("isMobileLogin") - 100 : js.find("isMobileLogin") + 400].replace("\n", " ")[:500])

# Search error message title display - login.error or similar
for pat in ["MISSING_FRAGMENTS", "errorMessages", "login.errors", "renderError"]:
    c = js.count(pat)
    if c:
        print(pat, c)
