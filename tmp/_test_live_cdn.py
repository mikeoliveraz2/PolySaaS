import requests

cdn_path = "/dose/sniff/4/native//static.hsappstatic.net/LoginUI/static-1.15478/bundles/project.js"
r = requests.get("http://127.0.0.1:8000" + cdn_path, timeout=30, allow_redirects=False)
print("status", r.status_code, "ctype", r.headers.get("Content-Type", "")[:40], "len", len(r.content))
