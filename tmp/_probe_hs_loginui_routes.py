"""Find which LoginUI route shows MISSING_FRAGMENTS on plain /login/."""
import re
import requests

js = requests.get(
    "https://static.hsappstatic.net/LoginUI/static-1.15500/bundles/project.js",
    timeout=30,
    headers={"Accept-Encoding": "identity"},
).text

# Google confirm component mount
pos = js.find("class yi extends")
print("yi class at", pos)
print(js[pos : pos + 800])

# Search error rendering - what maps error code to MISSING_FRAGMENTS display
for m in re.finditer(r'error:\s*["\'][A-Z_]+["\']', js):
    s = m.group(0)
    if "MISSING" in s or "MISMATCH" in s or "FRAGMENT" in s:
        print("error assign:", s)

# Find parseParams implementation
pp = js.find("parseParams")
print("\nparseParams at", pp)
print(js[pp - 100 : pp + 600])

# Search for router path /login/
for needle in ["/login/", 'path:"/login', "pathname===", "login.google", "CONFIRMATION_FAILED"]:
    i = 0
    n = 0
    while n < 3:
        i = js.find(needle, i)
        if i < 0:
            break
        print(f"\n--- {needle} @ {i} ---")
        print(js[max(0, i - 120) : i + 200].replace("\n", " ")[:320])
        i += 1
        n += 1
