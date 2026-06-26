import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

import requests
from django.db import connection
from dose.models import PassThroughEndpoint
from dose.polysniffer.sniff_handler_bridge import apply_native_sniff_rewrites

PATH = "/global-home/246571499"
PROXY = "/dose/sniff/4/native"

with connection.cursor() as c:
    c.execute('SET search_path TO "plysaast10", public')
ep = PassThroughEndpoint.objects.get(id=4)

class R:
    path_info = PROXY + PATH

raw = requests.get(
    "https://app-na2.hubspot.com" + PATH,
    headers={"Accept-Encoding": "identity"},
    timeout=30,
    allow_redirects=True,
)
print("upstream status", raw.status_code, "final", raw.url[:100])

body = apply_native_sniff_rewrites(
    raw.content,
    content_type=raw.headers.get("Content-Type", ""),
    request=R(),
    endpoint=ep,
    upstream_path=PATH,
    proxy_prefix=PROXY,
).decode("utf-8", errors="replace")

print("invalid login msg", "login url is invalid" in body.lower())
print("title", re.search(r"<title[^>]*>([^<]+)", body, re.I))
cdn = body.count("https://static.hsappstatic.net")
broken = body.count("/native//static")
proxied_cdn = len(re.findall(r"/native/static\.hsappstatic", body, re.I))
print("cdn https refs", cdn, "broken //static", broken, "proxied /native/static", proxied_cdn)
