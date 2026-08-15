from types import SimpleNamespace
from dose.passthrough.handlers.nextcloud_handler import NextcloudPassthroughHandler

h = NextcloudPassthroughHandler()
req = SimpleNamespace(_polysniffer_proxy_prefix="/pt/polysniff/3", _passthrough_endpoint=None)
css = b"body{--image-background-default:url('/apps/theming/img/background/kamil-porembinski-clouds.jpg');}"
out = h.rewrite_upstream_body(css, "text/css", req)
text = out.decode() if out else "NONE"
assert "/pt/polysniff/3/apps/theming/img/background/kamil-porembinski-clouds.jpg" in text, text
print("OK", text)
