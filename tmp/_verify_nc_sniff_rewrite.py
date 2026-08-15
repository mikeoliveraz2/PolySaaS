"""Verify sniff NC path rewrite + URL prefix (no live browser login)."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from types import SimpleNamespace
from django.test import RequestFactory
from dose.passthrough.handlers.nextcloud_handler import NextcloudPassthroughHandler
from dose.polysniffer.sniff_pt_proxy import _prefix_sniff_root_urls

# 1) Prefix helper
html = '<link href="/core/css/server.css"><script src="/dist/core-main.js"></script>'
out = _prefix_sniff_root_urls(html, "/pt/polysniff/3")
assert "/pt/polysniff/3/core/css/server.css" in out, out
assert "/pt/polysniff/3/dist/core-main.js" in out, out
print("OK prefix helper")

# 2) Sniff Referer → bare /core/css maps to /pt/polysniff/3/...
rf = RequestFactory()
req = rf.get("/core/css/server.css?v=1")
req.META["HTTP_REFERER"] = "http://127.0.0.1:8000/pt/polysniff/3/apps/files/"
endpoint = SimpleNamespace(endpoint_url="http://localhost:8888", slug="nextcloud", get_proxy_prefix=lambda: "/pt/admin/localhost:8888")
h = NextcloudPassthroughHandler()
ok = h.try_rewrite_incoming_path(req, endpoint)
assert ok is True, "expected rewrite"
assert req.path_info.startswith("/pt/polysniff/3/core/css/server.css"), req.path_info
print("OK sniff referer rewrite ->", req.path_info)

# 3) Admin path still used when Referer is Jazzmin (not sniff)
req2 = rf.get("/core/css/server.css")
req2.META["HTTP_REFERER"] = "http://127.0.0.1:8000/pt/admin/localhost:8888/apps/files/"
req2.COOKIES = {"ocabcdefghijkl": "sess"}
ok2 = h.try_rewrite_incoming_path(req2, endpoint)
assert ok2 is True, "admin rewrite expected"
assert req2.path_info.startswith("/pt/admin/localhost:8888/core/css/"), req2.path_info
print("OK admin referer rewrite ->", req2.path_info)

print("ALL CHECKS PASSED")
