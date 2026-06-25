import os
import re

import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

# Ensure handler + native processor registered
from dose.passthrough.handlers import hubspot_handler  # noqa: F401
from dose.polysniffer.sniff_handler_bridge import apply_native_sniff_rewrites

class _Ep:
    endpoint_url = "https://app-na2.hubspot.com"
    provider = "Custom"
    trigger_path = "app-na2.hubspot.com"
    menu_title = "Hubspot"
    slug = "hubspot"

class _Req:
    path_info = "/dose/sniff/4/native/login"
    is_secure = lambda self: False
    def get_host(self):
        return "localhost:8000"

html = requests.get(
    "https://app-na2.hubspot.com/login",
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30,
).content
out = apply_native_sniff_rewrites(
    html,
    content_type="text/html",
    request=_Req(),
    endpoint=_Ep(),
    upstream_path="/login",
    proxy_prefix="/dose/sniff/4/native",
)
text = out.decode("utf-8", "replace")
print("broken proxy cdn", text.count("/native//static.hsappstatic"))
print("https cdn", text.count("https://static.hsappstatic.net"))
for _, m in re.findall(r'(?:src|href)=(["\'])([^"\']+)\1', text):
    if "hsappstatic" in m or "/native//" in m:
        print(" ", m[:150])
