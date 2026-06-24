import re
import requests

r = requests.get("https://polysaas-mattermost.onrender.com/", timeout=30)
print("status", r.status_code, "len", len(r.text))
for pat in ("format=old", "config/client", "EnableSignIn"):
    print(pat, r.text.find(pat))

# Simulate native proxy config/client without format=old
r2 = requests.get(
    "https://polysaas-mattermost.onrender.com/api/v4/config/client",
    headers={"Accept": "application/json"},
    timeout=30,
)
print("config no format:", r2.status_code, r2.text[:120])

# With format=old
r3 = requests.get(
    "https://polysaas-mattermost.onrender.com/api/v4/config/client?format=old",
    timeout=30,
)
print("config format=old:", r3.status_code, "email", r3.json().get("EnableSignInWithEmail"))
