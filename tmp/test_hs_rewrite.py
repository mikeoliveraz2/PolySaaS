"""Unit test HubSpot HTML rewrite without Django."""
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Minimal stub so we can import rewrite without Django
class _StubHandler:
    def _should_proxy_path(self, path, proxy_prefix):
        return False

from dose.polysniffer.handlers.hubspot_native_sniff import (
    _rewrite_protocol_relative_cdn,
    _rewrite_hubspot_native_html,
)

SAMPLE = """
<link rel="stylesheet" href="//static.hsappstatic.net/home-redirect-ui/static/hubspot-theme.stable.css">
<link rel="stylesheet" href='//static2.hsappstatic.net/foo/bar.css'>
<script src="//static.hsappstatic.net/home-redirect-ui/static/main.js"></script>
"""

print("=== CDN only ===")
out = _rewrite_protocol_relative_cdn(SAMPLE)
print(out)
assert '.css""' not in out, "double quote in css"
assert 'https://static.hsappstatic.net' in out

print("=== full rewrite ===")
full = _rewrite_hubspot_native_html(
    SAMPLE,
    base_origin="https://app-na2.hubspot.com",
    proxy_prefix="/pt/admin/app.hubspot.com",
    handler=_StubHandler(),
)
print(full)
assert '.css""' not in full
assert '.js""' not in full
print("ALL OK")
