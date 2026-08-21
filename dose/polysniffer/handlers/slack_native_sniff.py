"""Slack — PolySniffer native sniff rewrites.

This keeps Slack app pages living under the native sniff proxy while directing
static assets at the upstream Slack origin. The goal is a simple native browser
capture flow for login and app navigation without using an iframe.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urlparse


def _base_origin(endpoint_url: str) -> str:
    parsed = urlparse((endpoint_url or "").strip())
    return f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""


def _is_html(content_type: str) -> bool:
    ct = (content_type or "").lower()
    return "text/html" in ct or "application/xhtml" in ct


def _rewrite_html_static_to_host(html: str, base_origin: str, proxy_prefix: str) -> str:
    html = re.sub(r"<base\b[^>]*>", "", html, flags=re.IGNORECASE)
    html = re.sub(
        r"(src|href)=(['\"])(/[^'\"]+)\2",
        lambda m: (
            m.group(0)
            if m.group(3).startswith(proxy_prefix)
            else f"{m.group(1)}={m.group(2)}{base_origin}{m.group(3)}{m.group(2)}"
        ),
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(
        r"(action=)(['\"])(/[^'\"]*)",
        lambda m: f"{m.group(1)}{m.group(2)}{proxy_prefix}{m.group(3)}{m.group(2)}",
        html,
        flags=re.IGNORECASE,
    )
    return html


def _inject_native_api_shim(html: str, base_origin: str, proxy_prefix: str) -> str:
    shim = f"""
<script data-polysniffer-slack-native="1">
(function() {{
  var BASE = {json.dumps(base_origin.rstrip('/'))};
  var PROXY = {json.dumps(proxy_prefix)};
  var ORIGIN = window.location.origin;
  function rewrite(url) {{
    if (typeof url !== 'string' || !url || url.indexOf('data:') === 0 || url.indexOf('blob:') === 0) return url;
    if (url.indexOf(BASE) === 0) return url;
    if (url.indexOf(ORIGIN) === 0) return url;
    if (url.charAt(0) === '/') return BASE + url;
    if (url.indexOf('//') === 0) return 'https:' + url;
    return url;
  }}
  var _fetch = window.fetch;
  window.fetch = function(input, init) {{
    if (typeof input === 'string') input = rewrite(input);
    else if (typeof Request !== 'undefined' && input instanceof Request) {{
      var req = new Request(rewrite(input.url), input);
      input = req;
    }}
    return _fetch.call(this, input, init);
  }};
  var _open = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function(method, url) {{
    return _open.call(this, method, rewrite(url));
  }};
}})();
</script>
"""
    if re.search(r"<head[^>]*>", html, flags=re.IGNORECASE):
        return re.sub(r"(?i)(<head[^>]*>)", r"\1" + shim, html, count=1)
    return shim + html


def process_slack_native_sniff(
    handler,
    body: bytes,
    content_type: str,
    request,
    *,
    endpoint_url: str,
    upstream_path: str,
    proxy_prefix: str,
) -> bytes | None:
    base_origin = _base_origin(endpoint_url)
    if not base_origin or not body or not _is_html(content_type):
        return None
    try:
        html = body.decode("utf-8")
    except UnicodeDecodeError:
        return body
    html = _rewrite_html_static_to_host(html, base_origin, proxy_prefix)
    html = _inject_native_api_shim(html, base_origin, proxy_prefix)
    return html.encode("utf-8")


def _register() -> None:
    from dose.passthrough.handlers.slack_handler import SlackPassthroughHandler
    from dose.polysniffer.sniff_handler_bridge import register_native_sniff_processor

    register_native_sniff_processor(
        SlackPassthroughHandler,
        process_slack_native_sniff,
    )


_register()
