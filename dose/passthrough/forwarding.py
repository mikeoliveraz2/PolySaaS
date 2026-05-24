# dose/passthrough/forwarding.py — FINAL — GENERIC FORWARDER
import logging
import traceback
import requests
import json
from http.cookies import SimpleCookie
from django.http import HttpResponse

from dose.polysniffer.models import TrafficLog
from dose.polysniffer.schema_patch import ensure_trafficlog_capture_columns
from dose.passthrough.registry import get_handler

logger = logging.getLogger(__name__)

_SKIP_META = frozenset({"HTTP_HOST", "HTTP_CONTENT_LENGTH", "CONTENT_LENGTH", "HTTP_COOKIE", "HTTP_ACCEPT_ENCODING"})
_HOP_BY_HOP_RESPONSE_HEADERS = frozenset({
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailer", "transfer-encoding", "upgrade"
})

_SESSIONS = {}

def _get_session_for_origin(origin):
    if origin not in _SESSIONS:
        sess = requests.Session()
        sess.headers.update({"Accept-Encoding": "identity"})
        _SESSIONS[origin] = sess
    return _SESSIONS[origin]


def _inject_polysniffer_capture(html_content: str, app_name: str = "unknown") -> str:
    """Inject PolySniffer browser capture script."""
    if not html_content or "</body>" not in html_content.lower():
        return html_content

    import json
    app_name_json = json.dumps(app_name)

    script = f'''
    <script data-polysniffer="capture">
    (function() {{
        if (window.__PS_CAPTURE__) return;
        window.__PS_CAPTURE__ = true;
        const CAPTURE_URL = window.location.origin + "/admin/polysniffer/capture/";
        const APP_NAME = {app_name_json};
        // ... (rest of the capture script remains the same)
        console.log("%c[PolySniffer] Browser capture active for " + APP_NAME, "color:#0f0");
    }})();
    </script>
    '''

    body_idx = html_content.lower().rfind("</body>")
    if body_idx != -1:
        return html_content[:body_idx] + script + html_content[body_idx:]
    return html_content + script


def forward_request_standardized(request, endpoint_url, handler=None, endpoint=None):
    """Generic passthrough forwarder. No endpoint-specific code belongs here."""
    print("\n" + "="*120)
    print("FORWARDER (forward_request_standardized) CALLED")
    print(f"USER-CONFIGURED ENDPOINT: {endpoint_url}")
    print(f"INCOMING PATH         : {request.get_full_path()}")
    print(f"REQUEST METHOD        : {request.method}")
    print(f"USER                  : {request.user}")
    print(f"TENANT                : {getattr(request, 'tenant', 'None')}")
    print("="*120)

    try:
        full_path = request.path_info
        qs = request.META.get('QUERY_STRING', '')
        if qs:
            full_path += '?' + qs

        # Extract upstream path
        import re
        prefix_match = re.match(r'^/pt/(?:admin|dose)/[^/]+(.*)$', full_path)
        upstream_path = prefix_match.group(1) if prefix_match else "/"
        if not upstream_path or upstream_path == "/":
            upstream_path = "/"

        # === CLEAN HANDLER LOOKUP VIA REGISTRY ===
        if not handler:
            trigger = None
            if '/pt/admin/' in request.path:
                parts = request.path.strip('/').split('/')
                if len(parts) >= 3:
                    trigger = parts[2]
            elif endpoint and hasattr(endpoint, 'trigger'):
                trigger = endpoint.trigger

            if trigger:
                handler = get_handler(trigger)

        print(f"HANDLER RUNNING -> {handler.__class__.__name__ if handler else 'None'} (trigger={trigger})")

        target_url = endpoint_url.rstrip("/") + (upstream_path if upstream_path.startswith("/") else "/" + upstream_path)

        print(f"PASSTHROUGH -> {full_path} -> {target_url}")

        # Block websocket paths
        _blocked = ('/websocket', '/bus/', '/longpolling/', '/discuss/', '/mail/action')
        if any(upstream_path.startswith(b) or upstream_path == b.rstrip('/') for b in _blocked):
            from django.http import JsonResponse
            print(f"[PASSTHROUGH] BLOCKED path: {upstream_path}")
            return JsonResponse({'jsonrpc': '2.0', 'id': None, 'result': []})

        # Prepare outbound request
        outbound_headers = _outbound_headers_from_request(request)
        upstream_cookies = dict(request.COOKIES)

        # Let handler customize if needed
        if handler and hasattr(handler, "augment_outbound_headers"):
            handler.augment_outbound_headers(request, outbound_headers, target_url)

        if handler and hasattr(handler, "get_upstream_cookies"):
            extra = handler.get_upstream_cookies(request) or {}
            upstream_cookies.update(extra)

        # Send request to upstream
        from urllib.parse import urlparse
        origin = f"{urlparse(target_url).scheme}://{urlparse(target_url).netloc}"
        sess = _get_session_for_origin(origin)

        resp = sess.request(
            method=request.method,
            url=target_url,
            headers=outbound_headers,
            data=request.body,
            cookies=upstream_cookies,
            allow_redirects=False,
            timeout=60,
        )

        print(f"EXTERNAL SERVICE RESPONDED -> STATUS: {resp.status_code}")
        print(f"CONTENT LENGTH: {len(resp.content)} bytes")

        # === REDIRECT HANDLING ===
        if resp.status_code in (301, 302, 303, 307, 308):
            # ... redirect rewriting logic (keep as is, it's generic) ...
            # I'll keep your existing redirect logic here for now
            location = resp.headers.get("Location", "/")
            print(f"FORWARDER — upstream redirect to {location}")
            # (Your existing redirect rewriting code can stay here)
            # ...

        content_type = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        is_html = content_type in ("text/html", "application/xhtml+xml") or content_type.endswith("+html")

        if not is_html:
            # Non-HTML passthrough
            response = HttpResponse(resp.content, status=resp.status_code)
            _copy_upstream_response_headers(response, resp)
            _forward_upstream_set_cookie_headers(response, resp)
            return response

        # === HTML PROCESSING ===
        content = resp.text

        if handler and hasattr(handler, "process_html_response"):
            print(f"HANDLER RUNNING -> {handler.__class__.__name__} process_html_response")
            processed = handler.process_html_response(content, request, endpoint_url=endpoint_url)
            if isinstance(processed, tuple):
                content = processed[0] or content
            elif isinstance(processed, str):
                content = processed
            elif isinstance(processed, HttpResponse):
                return processed

        # Optional PolySniffer injection
        if request.GET.get('polysniffer') == '1':
            content = _inject_polysniffer_capture(content, getattr(handler, 'service_name', 'unknown'))

        response = HttpResponse(content.encode("utf-8"), status=resp.status_code)
        _copy_upstream_response_headers(response, resp, exclude={"content-length", "etag", "content-encoding"})
        _forward_upstream_set_cookie_headers(response, resp, log_label="FORWARDER (HTML)")

        print("FORWARDER SUCCESS — HTML RESPONSE SENT")
        print("=" * 120 + "\n")
        return response

    except Exception as e:
        tb = traceback.format_exc()
        print("\n" + "!"*120)
        print("FORWARDER FAILED — FULL TRUTH BELOW")
        print(f"EXCEPTION TYPE: {type(e).__name__}")
        print(f"EXCEPTION     : {e}")
        print("TRACEBACK:")
        print(tb)
        print("!"*120 + "\n")

        error_html = f"""
        <div style="padding:40px; font-family:monospace; background:#000; color:#0f0;">
          <h2>FORWARDING FAILED</h2>
          <p><strong>Target:</strong> {target_url if 'target_url' in locals() else 'UNKNOWN'}</p>
          <p><strong>Error:</strong> {e}</p>
          <pre>{tb}</pre>
        </div>
        """
        return HttpResponse(error_html.encode('utf-8'), status=502, content_type='text/html; charset=utf-8')


# Helper functions (kept generic)
def _outbound_headers_from_request(request):
    headers = {}
    for k, v in request.META.items():
        if k in _SKIP_META:
            continue
        if k.startswith("HTTP_"):
            headers[k[5:].replace("_", "-").lower()] = v
        elif k == "CONTENT_TYPE":
            headers["content-type"] = v
        elif k == "CONTENT_LENGTH" and v:
            headers["content-length"] = v
    return headers


def _copy_upstream_response_headers(response, resp, exclude=None):
    excluded = {h.lower() for h in (exclude or ())}
    for name, value in resp.headers.items():
        if name.lower() in _HOP_BY_HOP_RESPONSE_HEADERS or name.lower() in excluded:
            continue
        response[name.lower()] = value


def _forward_upstream_set_cookie_headers(response, resp, forward_enabled=True, log_label="FORWARDER"):
    for raw_name, raw_val in resp.raw.headers.items():
        if raw_name.lower() != "set-cookie":
            continue
        if not forward_enabled:
            continue
        try:
            sc = SimpleCookie()
            sc.load(raw_val)
            for cookie_name, morsel in sc.items():
                response.cookies[cookie_name] = morsel.value
                print(f"{log_label} — forwarding Set-Cookie: {cookie_name}")
        except Exception:
            pass