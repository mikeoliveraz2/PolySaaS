import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

import requests
from dose.models import PassThroughEndpoint
from django.db import connection
from dose.polysniffer.sniff_handler_bridge import apply_native_sniff_rewrites

with connection.cursor() as c:
    c.execute('SET search_path TO "plysaast10", public')
ep = PassThroughEndpoint.objects.get(id=4)

class R:
    path_info = "/dose/sniff/4/native/login/"

for path in ("/login", "/login/", "/login?redirect_url=%2F"):
    raw = requests.get("https://app-na2.hubspot.com" + path, timeout=30, allow_redirects=True)
    body = apply_native_sniff_rewrites(
        raw.content,
        content_type=raw.headers.get("Content-Type", ""),
        request=R(),
        endpoint=ep,
        upstream_path=path.split("?")[0],
        proxy_prefix="/dose/sniff/4/native",
    ).decode("utf-8", errors="replace")
    invalid = "login URL is invalid" in body or "login url is invalid" in body.lower()
    print(f"\n=== upstream {path} status={raw.status_code} final={raw.url} invalid={invalid} ===")
    print("title snippet:", re.search(r"<title[^>]*>([^<]+)", body, re.I))
    # form actions
    actions = re.findall(r'action=(["\'])([^"\']+)\1', body, re.I)[:5]
    print("actions:", actions[:3])
    if invalid:
        idx = body.lower().find("login url is invalid")
        print(body[max(0, idx - 200) : idx + 200])
