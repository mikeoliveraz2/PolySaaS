"""Find what route mounts Google confirm component (yi) on login page."""
import re
import requests

js = requests.get(
    "https://static.hsappstatic.net/LoginUI/static-1.15500/bundles/project.js",
    timeout=30,
    headers={"Accept-Encoding": "identity"},
).text

# Find references near yi / GoogleLoginConfirm / googleLogin
for pat in [
    r"GoogleLogin[^\"]{0,40}",
    r"googleLogin[^\"]{0,40}",
    r"renderConfirmationFailed",
    r"CONFIRMING_LOGIN",
]:
    print("\n===", pat, "===")
    for m in re.finditer(pat, js):
        i = m.start()
        chunk = js[max(0, i - 80) : i + 120].replace("\n", " ")
        if "google" in chunk.lower() or "route" in chunk.lower() or "path" in chunk.lower():
            print(chunk[:200])

# Search Route components with login paths
print("\n=== Route path strings ===")
for m in re.finditer(r'path:\s*["\'](/login[^"\']*)["\']', js):
    print(m.group(1))

for m in re.finditer(r'["\'](/login/[a-zA-Z0-9_-]+)["\']', js):
    p = m.group(1)
    if "api" not in p and "forgot" not in p:
        print(p)
