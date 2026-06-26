import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

import requests
from dose.polysniffer.sniff_native_rewrite import rewrite_generic_native_fallback
from dose.polysniffer.sniff_handler_bridge import apply_native_sniff_rewrites
from dose.models import PassThroughEndpoint
from django.db import connection

with connection.cursor() as c:
    c.execute('SET search_path TO "plysaast10", public')
ep = PassThroughEndpoint.objects.get(id=4)
html = requests.get("https://app-na2.hubspot.com/login", timeout=30).content

# generic only
g = rewrite_generic_native_fallback(
    html,
    content_type="text/html",
    upstream_path="/login",
    proxy_prefix="/dose/sniff/4/native",
    endpoint_url=ep.endpoint_url,
).decode("utf-8", errors="replace")
print("generic broken count", g.count("/native//static"))

class R:
    path_info = "/dose/sniff/4/native/login"

full = apply_native_sniff_rewrites(
    html,
    content_type="text/html",
    request=R(),
    endpoint=ep,
    upstream_path="/login",
    proxy_prefix="/dose/sniff/4/native",
).decode("utf-8", errors="replace")
print("full broken count", full.count("/native//static"))
print("full https cdn count", full.count("https://static.hsappstatic.net"))
