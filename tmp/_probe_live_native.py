import re
import requests

url = "http://127.0.0.1:8000/dose/sniff/4/native/login"
r = requests.get(url, allow_redirects=True, timeout=30)
print("status", r.status_code, "final", r.url[:100], "len", len(r.text))
html = r.text
srcs = re.findall(r'(?:src|href)=(["\'])([^"\']+)\1', html, re.I)
cdn = [u for _, u in srcs if "static.hsappstatic.net" in u]
proxy_loginui = [u for _, u in srcs if "/native/" in u and "loginui" in u.lower()]
broken = [u for _, u in srcs if "/native//" in u]
print("cdn refs", len(cdn), "proxied loginui", len(proxy_loginui), "broken double-slash", len(broken))
if cdn[:2]:
    print("cdn sample", cdn[0][:100])
if proxy_loginui:
    print("loginui proxy", proxy_loginui[0][:120])
if broken:
    print("broken", broken[0][:120])

# paths that would 404 via app host
for _, u in srcs:
    if u.startswith("/dose/sniff/4/native/") and "hsappstatic" in u:
        print("CDN VIA PROXY:", u[:140])

test = "http://127.0.0.1:8000/dose/sniff/4/native//static.hsappstatic.net/LoginUI/static-1.15/bundles/project.js"
r2 = requests.get(test, timeout=15)
print("broken path test status", r2.status_code)
