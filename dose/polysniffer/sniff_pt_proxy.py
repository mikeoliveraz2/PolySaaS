"""
PolySniffer passthrough — public /pt/polysniff/{endpoint_host}/ routes.

Production handlers still run on internal /pt/admin/{trigger}/ paths; responses
are rewritten so redirects and shim PROXY_PREFIX stay on /pt/polysniff/ (iframe-safe).
"""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 Passthrough Workspace Iframe — 2026-06-24
#
# FIX 2026-08-21 (owner-approved, frozen-file exception): rewrite_polysniff_response()
# injects our own inline <script data-polysniffer-pt-client-capture> into every
# proxied HTML page but never stripped the proxied app's own
# Content-Security-Policy (header or <meta http-equiv> tag). Confirmed live in
# browser DevTools for Slack: its page ships a strict hash-allowlisted
# script-src CSP meta tag; our inline script has no matching hash/nonce, so the
# browser blocks it outright, Slack's own asset-loading watchdog then treats
# that as a failed load and force-reloads the whole client
# (?cdn_fallback=1&force_cold_boot=1) in a loop that never settles -- the
# reported "blank native pane" symptom. This is generic, app-agnostic
# stripping (any proxied app's CSP could block injected/rewritten content),
# not Slack-specific logic, so it belongs in this shared response-rewrite step.
# BINGO: PolySniffer CSP Strip For Injected Capture Script — 2026-08-21
#
# FIX 2026-08-21 (owner-approved): public prefix keyed by endpoint host, not
# PassThroughEndpoint.id — same identity as /pt/admin/<host>/ and the workspace
# shell. Row id remains only for internal capture ingest / session helpers.
# BINGO: PolySniffer Host-Keyed Polysniff URLs — 2026-08-21
from __future__ import annotations

from urllib.parse import urlparse

import json
import re

_CSP_HEADER_NAMES = ("Content-Security-Policy", "Content-Security-Policy-Report-Only")
_CSP_META_RE = re.compile(
    r"(?is)<meta[^>]+http-equiv\s*=\s*[\"']?content-security-policy[\"']?[^>]*>"
)


def _strip_csp(response) -> None:
    """Remove the proxied app's own CSP (header + meta tag) so our injected
    capture script and any rewritten URLs aren't blocked by it."""
    for header in _CSP_HEADER_NAMES:
        if header in response:
            del response[header]


def public_polysniff_prefix(endpoint_host: str) -> str:
    host = (endpoint_host or "").strip().strip("/")
    return f"/pt/polysniff/{host}"


def legacy_sniff_prefix(endpoint_id: int) -> str:
    return f"/dose/sniff/{endpoint_id}/passthrough"


def admin_prefix(trigger: str) -> str:
    return f"/pt/admin/{trigger}"


def internal_admin_path(trigger: str, subpath: str) -> str:
    sub = subpath or ""
    if sub and not sub.startswith("/"):
        sub = "/" + sub
    return f"{admin_prefix(trigger)}{sub}"


def _endpoint_trigger(endpoint) -> str:
    raw = (endpoint.endpoint_url or "").strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        return urlparse(raw).netloc
    return raw.split("/")[0]


def _inject_workspace_client_capture(html: str, endpoint_id: int) -> str:
    """Hook fetch/XHR in passthrough iframe — shim traffic bypasses server proxy."""
    if "data-polysniffer-pt-client-capture" in html:
        return html
    # Ingest route is still id-keyed under admin sniff urls (separate leftover).
    ingest = f"/admin/polysniffer/sniff/{endpoint_id}/workspace/ingest/"
    shim = f"""
<script data-polysniffer-pt-client-capture="1">
(function() {{
  var INGEST = {json.dumps(ingest)};
  function send(payload) {{
    try {{
      var blob = new Blob([JSON.stringify(payload)], {{type: 'application/json'}});
      if (navigator.sendBeacon && navigator.sendBeacon(INGEST, blob)) return;
    }} catch (e) {{}}
    fetch(INGEST, {{
      method: 'POST',
      credentials: 'same-origin',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(payload),
      keepalive: true
    }}).catch(function() {{}});
  }}
  function pathOf(url) {{
    try {{ return new URL(url, window.location.origin).pathname; }} catch (e) {{ return url; }}
  }}
  function log(method, url, status, ms) {{
    if (!url || url.indexOf(INGEST) !== -1) return;
    send({{
      method: method || 'GET',
      url: String(url).slice(0, 500),
      path: pathOf(url).slice(0, 500),
      status_code: status || 0,
      duration_ms: ms || 0
    }});
  }}
  var _f = window.fetch;
  window.fetch = function(input, init) {{
    var method = (init && init.method) || 'GET';
    var url = typeof input === 'string' ? input : (input && input.url) || '';
    var t0 = performance.now();
    return _f.apply(this, arguments).then(function(resp) {{
      log(method, url || (resp && resp.url) || '', resp && resp.status, performance.now() - t0);
      return resp;
    }}, function(err) {{
      log(method, url, 0, performance.now() - t0);
      throw err;
    }});
  }};
  var _xo = XMLHttpRequest.prototype.open;
  var _xs = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function(method, url) {{
    this._psMethod = method;
    this._psUrl = url;
    this._psT0 = performance.now();
    return _xo.apply(this, arguments);
  }};
  XMLHttpRequest.prototype.send = function() {{
    var xhr = this;
    xhr.addEventListener('loadend', function() {{
      log(xhr._psMethod, xhr._psUrl, xhr.status, performance.now() - (xhr._psT0 || performance.now()));
    }});
    return _xs.apply(this, arguments);
  }};
}})();
</script>
"""
    if re.search(r"(?i)<head[^>]*>", html):
        return re.sub(r"(?i)(<head[^>]*>)", r"\1" + shim, html, count=1)
    return shim + html


def rewrite_polysniff_response(
    response,
    *,
    endpoint_id: int,
    trigger: str,
    public_prefix: str,
    popup_login: bool = False,
):
    """Keep browser navigation on the PolySniffer public prefix (not /pt/admin/)."""
    admin_pf = admin_prefix(trigger)
    replacements = (
        (admin_pf, public_prefix),
        (legacy_sniff_prefix(endpoint_id), public_prefix),
        (f"/pt/polysniff/{endpoint_id}", public_prefix),
    )

    location = response.get("Location")
    if location:
        for old, new in replacements:
            if location.startswith(old):
                response["Location"] = new + location[len(old) :]
                break

    _strip_csp(response)

    content_type = (response.get("Content-Type") or "").lower()
    if hasattr(response, "content") and response.content and "text/html" in content_type:
        body = response.content.decode("utf-8", errors="ignore")
        for old, new in replacements:
            body = body.replace(old, new)
        body = _CSP_META_RE.sub("", body)
        if not popup_login:
            body = _inject_workspace_client_capture(body, endpoint_id)
        response.content = body.encode("utf-8")
        if "Content-Length" in response:
            response["Content-Length"] = len(response.content)

    response.xframe_options_exempt = True
    return response


def dispatch_polysniff_passthrough(request, endpoint_host: str, path: str = "", *, public_prefix: str | None = None):
    from dose.polysniffer.sniff_tenant import bind_request_tenant, get_sniff_capture_session
    from dose.polysniffer.views.core import get_endpoint_by_host

    if not request.user.is_staff:
        from django.http import HttpResponseForbidden

        return HttpResponseForbidden("Staff only")

    host = (endpoint_host or "").strip().strip("/")
    endpoint = get_endpoint_by_host(host, request)
    trigger = _endpoint_trigger(endpoint)
    endpoint_id = int(endpoint.pk)
    subpath = path or ""
    if subpath and not subpath.startswith("/"):
        subpath = "/" + subpath

    popup_login = (request.GET.get("ps_hs_popup") or "").strip() == "1"

    _bad_segs = {"undefined", "null", "nan"}
    if any(seg.lower() in _bad_segs for seg in (subpath or "").strip("/").split("/") if seg):
        from django.shortcuts import redirect as _redirect

        if popup_login:
            pub_early = (public_prefix or public_polysniff_prefix(host)).rstrip("/")
            return _redirect(f"{pub_early}/home/")
        from dose.polysniffer.sniff_native_embed import workspace_shell_prefix
        return _redirect(f"{workspace_shell_prefix(endpoint_id)}/home/")

    if popup_login:
        request._polysniffer_popup_login = True

    pub = (public_prefix or public_polysniff_prefix(host)).rstrip("/")
    request._polysniffer_endpoint_id = endpoint_id
    request._polysniffer_endpoint_host = host
    request._polysniffer_sniff_mode = "passthrough"
    request._polysniffer_proxy_prefix = pub
    bind_request_tenant(request)
    cap = get_sniff_capture_session(request, host)
    if cap:
        request._polysniffer_capture = cap

    admin_path = internal_admin_path(trigger, subpath)
    request.path_info = admin_path
    request.path = admin_path
    request.META["PATH_INFO"] = admin_path
    request._polysniffer_client_path = f"{pub}{subpath or '/'}"

    from dose.admin_views import pt_admin_generic_passthrough_view

    response = pt_admin_generic_passthrough_view(
        request,
        endpoint=trigger,
        subpath=subpath.lstrip("/") or None,
    )
    return rewrite_polysniff_response(
        response,
        endpoint_id=endpoint_id,
        trigger=trigger,
        public_prefix=pub,
        popup_login=popup_login,
    )
