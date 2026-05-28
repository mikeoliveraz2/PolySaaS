# dose/passthrough/forwarding.py — FINAL — PRINTS EVERYTHING — EXCEPTIONS SHOW TRUTH
import logging
import traceback
import requests
import json
import time
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)

_SKIP_META = frozenset({"HTTP_HOST", "HTTP_CONTENT_LENGTH", "CONTENT_LENGTH", "HTTP_COOKIE", "HTTP_ACCEPT_ENCODING"})


def _should_follow_upstream_redirects(handler, request, *, target_url, upstream_path):
    """Shared default is no internal redirect following for proxied requests."""
    if handler and hasattr(handler, "should_follow_upstream_redirects"):
        try:
            return bool(
                handler.should_follow_upstream_redirects(
                    request,
                    target_url=target_url,
                    upstream_path=upstream_path,
                )
            )
        except Exception as exc:
            logger.warning("should_follow_upstream_redirects failed: %s", exc, exc_info=True)
    return False


def _postprocess_upstream_response(
    handler,
    resp,
    request,
    *,
    endpoint_url,
    target_url,
    upstream_path,
    outbound_headers,
    upstream_cookies,
):
    """Handlers own endpoint-specific upstream response normalization."""
    if handler and hasattr(handler, "postprocess_upstream_response"):
        try:
            new_resp = handler.postprocess_upstream_response(
                resp,
                request,
                endpoint_url=endpoint_url,
                target_url=target_url,
                upstream_path=upstream_path,
                outbound_headers=outbound_headers,
                upstream_cookies=upstream_cookies,
            )
            if new_resp is not None:
                return new_resp
        except Exception as exc:
            logger.warning("postprocess_upstream_response failed: %s", exc, exc_info=True)
    return resp


def _should_forward_set_cookie_headers(handler, request, *, upstream_content_type, upstream_path, response_kind):
    """
    Shared default is to forward upstream Set-Cookie headers.
    Endpoint-specific exceptions must live on the handler, not in the forwarder.
    """
    if handler and hasattr(handler, "should_forward_set_cookie_headers"):
        try:
            return bool(
                handler.should_forward_set_cookie_headers(
                    request,
                    upstream_content_type=upstream_content_type,
                    upstream_path=upstream_path,
                    response_kind=response_kind,
                )
            )
        except Exception as exc:
            logger.warning("should_forward_set_cookie_headers failed: %s", exc, exc_info=True)
    return True


def _outbound_headers_from_request(request):
    headers = {}
    for k, v in request.META.items():
        if k in _SKIP_META:
            continue
        if k.startswith("HTTP_"):
            # Django stores headers as HTTP_HEADER_NAME; convert back to Header-Name
            headers[k[5:].replace("_", "-").title()] = v
        elif k == "CONTENT_TYPE":
            headers["Content-Type"] = v
        elif k == "CONTENT_LENGTH" and v:
            headers["Content-Length"] = v
    return headers


def _resolve_upstream_target_url(endpoint_url, upstream_subpath, handler=None):
    """
    Build the upstream URL for a proxied path. Handlers may override (e.g. Odoo uses the
    full configured endpoint for the initial document only, and origin + path for /web, /bus, …).
    """
    clean = upstream_subpath if upstream_subpath not in (None, "") else "/"
    if not isinstance(clean, str):
        clean = "/"
    if not clean.startswith("/"):
        clean = "/" + clean
    if handler is not None and hasattr(handler, "upstream_url_for_subpath"):
        try:
            resolved = handler.upstream_url_for_subpath(endpoint_url, clean)
        except Exception:
            logger.warning("upstream_url_for_subpath failed", exc_info=True)
            resolved = None
        if resolved:
            return resolved
    return endpoint_url.rstrip("/") + clean


def _origins_equivalent_for_upstream_fetch(origin_a: str, origin_b: str) -> bool:
    """
    Same-origin check for redirect following in fetch_upstream_index_html.

    Odoo (and other local services) often emit Location with 127.0.0.1 while the
    configured endpoint uses localhost (or vice versa). urllib treats those as
    different origins, which incorrectly yields a REDIRECT: sentinel and an empty
    display shell.
    """
    from urllib.parse import urlparse

    def _key(origin: str):
        p = urlparse(origin)
        scheme = (p.scheme or "http").lower()
        host = (p.hostname or "").lower()
        if host in ("127.0.0.1", "localhost", "::1", "host.docker.internal"):
            host = "__loopback__"
        port = p.port
        if port is None:
            port = 443 if scheme == "https" else 80
        return (scheme, host, port)

    try:
        return _key(origin_a) == _key(origin_b)
    except Exception:
        return origin_a == origin_b


def _is_initial_page_load(request):
    """Detect browser navigation vs API/asset request."""
    xrw = request.headers.get('X-Requested-With', '')
    if xrw == 'XMLHttpRequest':
        return False
    accept = request.headers.get('Accept', '')
    if 'text/html' not in accept:
        return False
    last_segment = request.path_info.split('/')[-1]
    if '.' in last_segment:
        ext = last_segment.split('.')[-1].lower()
        if ext in ('js', 'css', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'ico', 'woff', 'woff2', 'ttf', 'eot', 'map'):
            return False
    api_prefixes = ('/api/', '/plugins/', '/boards/', '/calls/', '/bus/', '/websocket')
    for prefix in api_prefixes:
        if prefix in request.path_info:
            return False
    return True


def _extract_head_and_body(html):
    """Extract <head> and <body> content from full HTML document."""
    import re
    head_content = ''
    body_content = html
    head_match = re.search(r'<head[^>]*>(.*?)</head>', html, re.DOTALL | re.IGNORECASE)
    if head_match:
        head_content = head_match.group(1)
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
    if body_match:
        body_content = body_match.group(1)
    elif '<body' in html.lower():
        body_start = re.search(r'<body[^>]*>', html, re.IGNORECASE)
        if body_start:
            body_content = html[body_start.end():]
            body_content = re.sub(r'</html>\s*$', '', body_content, flags=re.IGNORECASE)
    return head_content, body_content


def _wrap_in_admin_template(request, response, trigger, endpoint):
    """Wrap raw proxied HTML in admin template for embedded display."""
    content_type = response.get('Content-Type', '')
    if 'text/html' not in content_type:
        return response
    try:
        raw_html = response.content.decode('utf-8', errors='ignore')
    except Exception:
        return response
    if not raw_html or len(raw_html) < 100:
        return response
    norm = trigger.strip('/')
    embed_title = norm.split('.')[0].replace('-', ' ').title()
    embed_src = f'/pt/admin/{norm}/'
    head_content, body_content = _extract_head_and_body(raw_html)
    embed_body = mark_safe(
        f'<div class="polysaas-passthrough-scope" data-polysaas-embed-trigger="{norm}">'
        f'{body_content}</div>'
    )
    embed_head = mark_safe(head_content)
    upstream_path = getattr(request, '_passthrough_upstream_path', '/web')
    try:
        wrapped_html = render_to_string(
            'admin/passthrough_embed.html',
            {
                'embed_src': embed_src,
                'embed_title': embed_title,
                'embed_head': embed_head,
                'embed_body': embed_body,
                'upstream_path': upstream_path,
            },
            request=request,
        )
        wrapped_response = HttpResponse(wrapped_html, status=response.status_code)
        wrapped_response['Content-Type'] = 'text/html; charset=utf-8'
        wrapped_response['X-Frame-Options'] = 'ALLOWALL'
        wrapped_response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        for cookie_name in response.cookies:
            wrapped_response.cookies[cookie_name] = response.cookies[cookie_name].value
            wrapped_response.cookies[cookie_name]['path'] = response.cookies[cookie_name].get('path', '/')
            wrapped_response.cookies[cookie_name]['samesite'] = 'Lax'
        return wrapped_response
    except Exception:
        return response


def fetch_upstream_index_html(
    request, endpoint_url, upstream_subpath="/", handler=None, fetch_debug=None
):
    """
    GET upstream HTML mimicking a real browser request.
    Injects any app-specific cookies (e.g. MMAUTHTOKEN) via handler.get_upstream_cookies().
    If the upstream returns a 3xx redirect the redirect target URL is returned as a string
    prefixed with 'REDIRECT:' so the caller can pass it straight through to the browser.

    If ``fetch_debug`` is a dict, it is filled with failure details (error message, HTTP status,
    last URL) when this function returns "".
    """
    def _fail(**kwargs):
        if fetch_debug is not None:
            fetch_debug.update(kwargs)

    clean = upstream_subpath or "/"
    if not clean.startswith("/"):
        clean = "/" + clean
    target_url = _resolve_upstream_target_url(endpoint_url, clean, handler=handler)

    # Merge browser cookies with any app-specific cookies the handler wants to inject.
    # Browser cookies take priority — after a manual login the browser has the fresh
    # session token; the server's cached token may be stale.
    upstream_cookies = dict(request.COOKIES)
    if handler and hasattr(handler, "filter_cookies_for_upstream"):
        try:
            upstream_cookies = handler.filter_cookies_for_upstream(request, upstream_cookies)
        except Exception as _fc_exc:
            logger.warning("filter_cookies_for_upstream (fetch_upstream) failed: %s", _fc_exc)
    if handler and hasattr(handler, "get_upstream_cookies"):
        try:
            extra = handler.get_upstream_cookies(request) or {}
            for k, v in extra.items():
                if k not in upstream_cookies:   # don't overwrite what the browser already has
                    upstream_cookies[k] = v
        except Exception as exc:
            logger.warning("get_upstream_cookies failed: %s", exc)

    # Follow same-origin redirects automatically (up to 5 hops) so that apps like Odoo
    # whose root "/" redirects through "/odoo" before landing on the actual HTML are handled.
    # Cross-origin redirects are returned as REDIRECT: sentinels for the caller to handle.
    from urllib.parse import urlparse as _up
    _origin = f"{_up(target_url).scheme}://{_up(target_url).netloc}"
    _current_url = target_url
    resp = None

    hop_headers = _outbound_headers_from_request(request)
    if handler and hasattr(handler, "augment_outbound_headers"):
        try:
            handler.augment_outbound_headers(request, hop_headers, _current_url)
        except Exception as _aug_exc:
            logger.warning("augment_outbound_headers (fetch_upstream) failed: %s", _aug_exc)

    for _hop in range(15):
        try:
            print(f"\n{'>'*60}")
            print(f"[FETCH_UPSTREAM] OUTBOUND REQUEST Hop {_hop}:")
            print(f"  URL: {_current_url}")
            print(f"  Headers: {dict(hop_headers)}")
            print(f"  Cookies: {dict(upstream_cookies)}")
            print(f"{'>'*60}")
            resp = requests.get(
                _current_url,
                headers=hop_headers,
                cookies=upstream_cookies,
                allow_redirects=False,
                timeout=60,
            )
            print(f"{'<'*60}")
            print(f"[FETCH_UPSTREAM] RESPONSE:")
            print(f"  Status: {resp.status_code}")
            print(f"  Headers: {dict(resp.headers)}")
            print(f"{'<'*60}")
        except Exception as e:
            logger.warning("fetch_upstream_index_html %s failed: %s", _current_url, e)
            _fail(error=str(e), url=_current_url, phase="request_exception")
            return ""
        
        # Check if we got a redirect
        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location", "")
            print(f"[FETCH_UPSTREAM] Redirect to: {location}")
            if not location:
                break
            # Make relative URLs absolute (use *current* URL so multi-hop redirects stay consistent)
            if location.startswith("/"):
                _cur = _up(_current_url)
                location = f"{_cur.scheme}://{_cur.netloc}{location}"
            # Check if same-origin
            loc_parsed = _up(location)
            loc_origin = f"{loc_parsed.scheme}://{loc_parsed.netloc}"
            if not _origins_equivalent_for_upstream_fetch(loc_origin, _origin):
                # Cross-origin redirect - return as sentinel for caller
                print(f"[FETCH_UPSTREAM] Cross-origin redirect, returning sentinel")
                _fail(
                    phase="cross_origin_redirect",
                    status=resp.status_code,
                    location=location,
                    url=_current_url,
                )
                return f"REDIRECT:{resp.status_code}:{location}"
            # Same-origin - follow it (refresh Host / proxy headers for the new URL)
            _current_url = location
            if loc_parsed.netloc:
                hop_headers["Host"] = loc_parsed.netloc
            if handler and hasattr(handler, "augment_outbound_headers"):
                try:
                    handler.augment_outbound_headers(request, hop_headers, _current_url)
                except Exception as _aug2:
                    logger.warning(
                        "augment_outbound_headers (fetch redirect hop) failed: %s", _aug2
                    )
            continue
        else:
            # Not a redirect - we're done
            break
    
    if resp is None or resp.status_code != 200:
        status = resp.status_code if resp else "NO_RESPONSE"
        logger.warning(
            "fetch_upstream_index_html %s -> status %s", target_url, status
        )
        print(f"[FETCH_UPSTREAM] Final status {status} - returning empty")
        snippet = ""
        try:
            if resp is not None and resp.content:
                snippet = resp.content[:400].decode("utf-8", errors="replace")
        except Exception:
            pass
        _fail(
            phase="non_200",
            status=status,
            url=_current_url if resp is not None else target_url,
            body_preview=snippet,
        )
        return ""
    
    print(f"\n{'='*60}")
    print(f"[FETCH_UPSTREAM] FINAL SUCCESS - Got {len(resp.content)} bytes")
    print(f"[FETCH_UPSTREAM] Response preview (first 1000 chars):")
    print(f"{'='*60}")
    print(resp.content[:1000].decode('utf-8', errors='replace'))
    print(f"{'='*60}")

    # ── PolySniffer Capture (Initial HTML) ─────────────────────────────
    # try:
    #     from dose.polysniffer.models import TrafficLog
    #     from django.contrib.auth.models import AnonymousUser
    #     from django.db import connection
    #
    #     capture_user = request.user if (request.user and not isinstance(request.user, AnonymousUser)) else None
    #
    #     app_name = "unknown"
    #     if handler:
    #         app_name = handler.__class__.__name__.lower().replace("passthroughhandler", "")
    #
    #     tenant = getattr(request, "tenant", None)
    #     if tenant:
    #         with connection.cursor() as cur:
    #             cur.execute(f"SET search_path TO {tenant.schema_name}, public;")
    #
    #     ensure_trafficlog_capture_columns(request)
    #     TrafficLog.objects.create(
    #         method="GET",
    #         url=target_url,
    #         path=clean,
    #         headers=_outbound_headers_from_request(request),
    #         cookies=upstream_cookies,
    #         query_params=dict(request.GET),
    #         body="",
    #         status_code=resp.status_code,
    #         response_headers=dict(resp.headers),
    #         response_body=resp.content.decode("utf-8", errors="ignore"),
    #         response_size=len(resp.content),
    #         endpoint_name=app_name,
    #         user=capture_user,
    #         duration_ms=0,
    #         capture_source=TrafficLog.CAPTURE_PASSTHROUGH,
    #         client_path=getattr(request, "path_info", "") or "",
    #     )
    #     print(f"POLY SNIFFER — Captured Initial HTML for {app_name} in schema {tenant.schema_name if tenant else 'public'}")
    # except Exception as ps_exc:
    #     print(f"POLY SNIFFER — Initial HTML capture failed: {ps_exc}")
    # ───────────────────────────────────────────────────────────────────


def forward_request_standardized(request, endpoint_url, handler=None, endpoint=None, trigger=None):
    # PRINT EVERYTHING — ALWAYS — NO MERCY
    print("\n" + "="*120)
    print("FORWARDER (forward_request_standardized) CALLED")
    print(f"USER-CONFIGURED ENDPOINT: {endpoint_url}")
    print(f"INCOMING PATH         : {request.get_full_path()}")
    print(f"REQUEST METHOD        : {request.method}")
    print(f"USER                  : {request.user}")
    print(f"TENANT                : {getattr(request, 'tenant', 'None')}")
    print("="*120)

    try:
        # Use request.path_info (may be rewritten by ExternalPassthroughMiddleware for native
        # Odoo paths like /web/login -> /pt/admin/odoo/web/login) rather than get_full_path()
        # which reads request.META['PATH_INFO'] and never sees the rewritten path_info attribute.
        full_path = request.path_info
        qs = request.META.get('QUERY_STRING', '')
        if qs:
            full_path += '?' + qs

        # Generic prefix stripping: /pt/{admin|dose}/{trigger}/subpath -> /subpath
        import re
        prefix_match = re.match(r'^/pt/(?:admin|dose)/[^/]+(.*)$', full_path)
        if prefix_match:
            clean = prefix_match.group(1)
            if not clean or clean == "/":
                clean = "/"
            if not clean.startswith("/"):
                clean = "/" + clean
            upstream_path = clean
            target_url = _resolve_upstream_target_url(endpoint_url, clean, handler=handler)
            print(f"PASSTHROUGH -> {full_path} -> {target_url}")
        else:
            upstream_path = "/"
            target_url = endpoint_url
            print(f"PASSTHROUGH -> USING ENDPOINT ROOT: {target_url}")

        # Store on request for orchestration bar display
        request._passthrough_upstream_path = upstream_path

        # Block websocket/bus/discuss paths server-side — they crash through proxy
        _blocked = ('/websocket', '/bus/', '/longpolling/', '/discuss/', '/mail/action')
        if any(upstream_path.startswith(b) or upstream_path == b.rstrip('/') for b in _blocked):
            from django.http import JsonResponse as _JR
            print(f"[PASSTHROUGH] BLOCKED path: {upstream_path}")
            return _JR({'jsonrpc': '2.0', 'id': None, 'result': []})

        # Allow handler to intercept root/display requests before upstream fetch
        if trigger and handler and hasattr(handler, 'try_root_display_shell_response'):
            shell = handler.try_root_display_shell_response(request, endpoint, trigger)
            if shell is not None:
                print(f"[FORWARDER] Handler display shell returned for root — returning directly")
                return shell

        print(f"SENDING REQUEST TO -> {target_url}")

        # Never forward the browser's Host (e.g. localhost:8000); upstream must see its own host.
        outbound_headers = _outbound_headers_from_request(request)
        outbound_headers["Accept-Encoding"] = "identity"

        if handler and hasattr(handler, "augment_outbound_headers"):
            try:
                handler.augment_outbound_headers(request, outbound_headers, target_url)
            except Exception as _aug_exc:
                logger.warning("augment_outbound_headers failed: %s", _aug_exc)

        # Merge browser cookies with any app-specific cookies the handler wants to inject.
        # Browser cookies take priority — after a manual login the browser has the fresh
        # session token; the server's cached token may be stale.
        upstream_cookies = dict(request.COOKIES)
        if handler and hasattr(handler, "filter_cookies_for_upstream"):
            try:
                upstream_cookies = handler.filter_cookies_for_upstream(request, upstream_cookies)
            except Exception as _fc_exc:
                logger.warning("filter_cookies_for_upstream failed: %s", _fc_exc)
        if handler and hasattr(handler, "get_upstream_cookies"):
            try:
                extra = handler.get_upstream_cookies(request) or {}
                for k, v in extra.items():
                    if k not in upstream_cookies:   # don't overwrite what the browser already has
                        upstream_cookies[k] = v
            except Exception as exc:
                logger.warning("get_upstream_cookies failed: %s", exc)
        if handler and hasattr(handler, "override_upstream_cookies"):
            try:
                overrides = handler.override_upstream_cookies(request, target_url) or {}
                for k, v in overrides.items():
                    upstream_cookies[k] = v
                    print(f"[FORWARDER] override_upstream_cookies: {k}=<redacted>")
            except Exception as exc:
                logger.warning("override_upstream_cookies failed: %s", exc)

        # Allow handler to rewrite the outgoing request body (e.g. strip Django csrf_token for Odoo login)
        outbound_body = request.body
        if handler and hasattr(handler, "get_request_body"):
            try:
                rewritten = handler.get_request_body(request, target_url)
                if rewritten is not None:
                    outbound_body = rewritten
            except Exception as _body_exc:
                logger.warning("get_request_body failed: %s", _body_exc)

        # Debug: for login requests, print exactly what is going to upstream
        if "login" in target_url.lower():
            print("=== LOGIN FORWARD DEBUG ===")
            print(f"TARGET            : {target_url}")
            print(f"Cookie header sent: {'Cookie' in outbound_headers}")
            print(f"Cookies param     : { {k: v[:8]+'...' if v and len(v)>8 else v for k,v in upstream_cookies.items()} }")
            print(f"Body preview      : {outbound_body[:200] if outbound_body else '(empty)'}")
            print("===========================")

        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=outbound_headers,
            data=outbound_body,
            cookies=upstream_cookies,
            allow_redirects=_should_follow_upstream_redirects(
                handler,
                request,
                target_url=target_url,
                upstream_path=upstream_path,
            ),
            stream=False,
            timeout=60,
        )

        resp = _postprocess_upstream_response(
            handler,
            resp,
            request,
            endpoint_url=endpoint_url,
            target_url=target_url,
            upstream_path=upstream_path,
            outbound_headers=outbound_headers,
            upstream_cookies=upstream_cookies,
        )

        print(f"EXTERNAL SERVICE RESPONDED -> STATUS: {resp.status_code}")
        print(f"CONTENT LENGTH: {len(resp.content)} bytes")
        preview_bytes = resp.content[:500] if resp.content else b""
        print(f"CONTENT PREVIEW: {preview_bytes.decode('utf-8', errors='ignore')}")
        if '/odoo/apps' in target_url:
            print(f"[ODOO APPS DEBUG] status={resp.status_code}, len={len(resp.content)}, preview={preview_bytes[:200].decode('utf-8', errors='ignore')}")

        try:
            from dose.passthrough.stream_debug import log_upstream_response_if_debug

            log_upstream_response_if_debug(
                request,
                endpoint,
                upstream_path=upstream_path,
                target_url=target_url,
                resp=resp,
            )
        except Exception as _sd_exc:
            print(f"[PT-STREAM-DEBUG] upstream log error (non-blocking): {_sd_exc}")

        # ── PolySniffer Capture (Step 1) ───────────────────────────────────
        try:
            # Determine app name from path or handler
            app_name = "unknown"
            if handler:
                app_name = handler.__class__.__name__.lower().replace("passthroughhandler", "")
            
            # If still unknown, try parsing from path /pt/admin/{app}/...
            if app_name == "unknown" and "/pt/admin/" in request.path:
                parts = request.path.split("/")
                if len(parts) > 3:
                    app_name = parts[3]

            from django.contrib.auth.models import AnonymousUser
            capture_user = request.user if (request.user and not isinstance(request.user, AnonymousUser)) else None

            # Ensure we are in the correct schema for the tenant
            from django.db import connection
            tenant = getattr(request, "tenant", None)
            if tenant:
                with connection.cursor() as cur:
                    cur.execute(f"SET search_path TO {tenant.schema_name}, public;")

            # try:
            #     ensure_trafficlog_capture_columns(request)
            # except Exception as _patch_exc:
            #     print(f"[PASSTHROUGH] ensure_trafficlog_capture_columns: {_patch_exc}")
            #
            # TrafficLog.objects.create(...)
            # print(f"POLY SNIFFER — Captured {request.method} {upstream_path} for {app_name} in schema {tenant.schema_name if tenant else 'public'}")
            pass
        except Exception as ps_exc:
            print(f"POLY SNIFFER — Capture failed (non-blocking): {ps_exc}")

        # ── Orchestration Hook: fire for both REQ (outgoing) and RES (response received) ──
        try:
            from dose.passthrough.orchestration_hook import check_orchestration_trigger
            from dose.utils import get_current_tenant
            _orch_tenant = tenant or get_current_tenant(request)
            print(f"[ORCHESTRATION HOOK] tenant={_orch_tenant}, path={upstream_path}")
            check_orchestration_trigger(request, upstream_path, app_name, _orch_tenant,
                                        direction='REQ')
            check_orchestration_trigger(request, upstream_path, app_name, _orch_tenant,
                                        direction='RES', upstream_response=resp)
        except Exception as orch_exc:
            print(f"[ORCHESTRATION HOOK] Non-blocking error: {orch_exc}")
        # ───────────────────────────────────────────────────────────────────

        # CRITICAL: Rewrite redirects to go through the proxy, NOT direct to upstream.
        # This ensures all traffic flows through /pt/admin/{app}/ for PolySniffer and orchestration.
        # DO NOT pass redirects directly to upstream - that bypasses the entire PolySaaS value.
        if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location", "/")
            print(f"FORWARDER — upstream {resp.status_code} redirect to {location}")
            
            # Extract the proxy prefix from the original request path (e.g., /pt/admin/mattermost)
            # so we can prepend it to the redirect location
            original_path = request.path_info
            proxy_prefix = ""
            if original_path.startswith("/pt/"):
                # Extract /pt/admin/{app}/ from the path
                parts = original_path.strip("/").split("/")
                if len(parts) >= 3:
                    proxy_prefix = f"/{parts[0]}/{parts[1]}/{parts[2]}"  # /pt/admin/mattermost
            
            from urllib.parse import urlparse as _up
            p = _up(endpoint_url)
            upstream_origin = f"{p.scheme}://{p.netloc}"
            
            # Rewrite the location to go through the proxy
            from urllib.parse import urlparse as _ulp
            _loc_parsed = _ulp(location)
            _polysaas_host = request.get_host()  # e.g. localhost:8000

            if location.startswith(upstream_origin):
                # Absolute URL to upstream - strip origin and prepend proxy prefix
                rel_path = location[len(upstream_origin):]
                if not rel_path.startswith("/"):
                    rel_path = "/" + rel_path
                # Guard against double-prefix (upstream already injected proxy path via overwritewebroot)
                if not rel_path.startswith(proxy_prefix):
                    location = proxy_prefix + rel_path
                else:
                    location = rel_path
            elif _loc_parsed.netloc and _loc_parsed.netloc == _polysaas_host:
                # Absolute URL pointing back at PolySaaS itself — use the path as-is
                # (Nextcloud with overwritehost=localhost:8000 does this)
                location = _loc_parsed.path
                if _loc_parsed.query:
                    location += "?" + _loc_parsed.query
            elif location.startswith("/"):
                # Relative path - prepend proxy prefix only if not already prefixed
                # (Nextcloud with overwritewebroot bakes the proxy prefix into Location headers)
                if not location.startswith(proxy_prefix):
                    location = proxy_prefix + location
            elif location.startswith(("http://", "https://")):
                # Absolute URL to different origin - pass through unchanged (external redirect)
                pass
            else:
                # Relative path without leading slash
                location = proxy_prefix + "/" + location
            
            print(f"FORWARDER — rewritten redirect to {location} (proxy prefix: {proxy_prefix})")
            redirect_response = HttpResponse(status=resp.status_code)
            redirect_response["Location"] = location

            # Forward Set-Cookie headers from the upstream redirect response.
            # Critical for login flows: Nextcloud/Odoo set the session cookie on the
            # 302 login response — without this the browser never gets authenticated.
            from http.cookies import SimpleCookie as _SC
            for _rh_name, _rh_val in resp.raw.headers.items():
                if _rh_name.lower() != "set-cookie":
                    continue
                try:
                    _sc = _SC()
                    _sc.load(_rh_val)
                    for _cn, _cm in _sc.items():
                        redirect_response.cookies[_cn] = _cm.value
                        redirect_response.cookies[_cn]["path"] = _cm.get("path") or "/"
                        redirect_response.cookies[_cn]["samesite"] = "Lax"
                        print(f"FORWARDER — forwarding Set-Cookie on redirect: {_cn}")
                except Exception as _ce:
                    print(f"FORWARDER — Set-Cookie parse error on redirect: {_ce}")

            return redirect_response

        content_type = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        is_html = content_type in ("text/html", "application/xhtml+xml") or content_type.endswith(
            "+html"
        )

        # API, JS, CSS, images, fonts, etc. must pass through unchanged (not forced to text/html).
        # Handlers may still rewrite selected bodies (e.g. Mattermost /api/v4/config/client JSON).
        if not is_html:
            body = resp.content
            body_rewritten = False
            if handler and hasattr(handler, "rewrite_upstream_body"):
                try:
                    new_body = handler.rewrite_upstream_body(
                        body,
                        content_type,
                        request,
                        endpoint_url=endpoint_url,
                        upstream_path=upstream_path,
                    )
                    if new_body is not None:
                        body = new_body
                        body_rewritten = True
                        print("FORWARDER — rewrite_upstream_body applied (non-HTML body modified)")
                except Exception as rw_exc:
                    logger.warning("rewrite_upstream_body failed: %s", rw_exc, exc_info=True)

            response = HttpResponse(body, status=resp.status_code)
            upstream_ct = resp.headers.get("Content-Type")
            if upstream_ct:
                response["Content-Type"] = upstream_ct
            _copy_headers = (
                "Cache-Control",
                "ETag",
                "Last-Modified",
                "X-Frame-Options",
                "X-Content-Type-Options",
                "X-XSS-Protection",
                "Referrer-Policy",
                "Content-Security-Policy",
                "Strict-Transport-Security",
                "Token",       # Mattermost login response — SPA reads this to get the session token
                "X-Version-Id",   # Mattermost SPA version check
                "X-Request-Id",   # Mattermost request tracking
            )
            if body_rewritten:
                _copy_headers = tuple(h for h in _copy_headers if h != "ETag")
            for hk in _copy_headers:
                if hk in resp.headers:
                    response[hk] = resp.headers[hk]

            # Handlers own any endpoint-specific Set-Cookie policy.
            _forward_set_cookie = _should_forward_set_cookie_headers(
                handler,
                request,
                upstream_content_type=upstream_ct,
                upstream_path=upstream_path,
                response_kind="non-html",
            )
            from http.cookies import SimpleCookie
            for raw_name, raw_val in resp.raw.headers.items():
                if raw_name.lower() != "set-cookie":
                    continue
                if not _forward_set_cookie:
                    print(f"FORWARDER — handler suppressed Set-Cookie ({upstream_ct})")
                    continue
                try:
                    sc = SimpleCookie()
                    sc.load(raw_val)
                    for cookie_name, morsel in sc.items():
                        response.cookies[cookie_name] = morsel.value
                        response.cookies[cookie_name]["path"] = morsel.get("path") or "/"
                        response.cookies[cookie_name]["samesite"] = "Lax"
                        # intentionally omit httponly and domain
                        print(f"FORWARDER — forwarding Set-Cookie: {cookie_name}=<redacted>")
                except Exception as sc_exc:
                    print(f"FORWARDER — Set-Cookie parse error: {sc_exc}")
            response["X-Frame-Options"] = "ALLOWALL"
            print("FORWARDER SUCCESS — BINARY/TEXT PASSTHROUGH (non-HTML)")
            print("=" * 120 + "\n")
            return response

        content = resp.text

        if handler:
            print(f"HANDLER RUNNING -> {handler.__class__.__name__}")
            processed = handler.process_html_response(content, request, endpoint_url=endpoint_url)
            if isinstance(processed, HttpResponse):
                print("HANDLER RETURNED HttpResponse — RETURNING DIRECTLY")
                return processed
            if isinstance(processed, tuple):
                content = processed[0] if processed[0] else content
                print("HANDLER FINISHED (tuple) — CONTENT MODIFIED")
            else:
                content = processed
                print("HANDLER FINISHED — CONTENT MODIFIED")
        else:
            print("NO HANDLER — RETURNING HTML AS-IS")

        response = HttpResponse(content.encode("utf-8"), status=resp.status_code)
        response["Content-Type"] = resp.headers.get("Content-Type", "text/html; charset=utf-8")
        response["Content-Encoding"] = "identity"
        response["X-Frame-Options"] = "ALLOWALL"
        for csp_hdr in ("Content-Security-Policy", "Content-Security-Policy-Report-Only"):
            try:
                del response[csp_hdr]
            except KeyError:
                pass

        # Forward Set-Cookie headers from HTML responses too (critical for Nextcloud login)
        # The session cookie must match the requesttoken embedded in the HTML
        from http.cookies import SimpleCookie
        for raw_name, raw_val in resp.raw.headers.items():
            if raw_name.lower() != "set-cookie":
                continue
            try:
                sc = SimpleCookie()
                sc.load(raw_val)
                for cookie_name, morsel in sc.items():
                    response.cookies[cookie_name] = morsel.value
                    response.cookies[cookie_name]["path"] = morsel.get("path") or "/"
                    response.cookies[cookie_name]["samesite"] = "Lax"
                    print(f"FORWARDER — forwarding Set-Cookie from HTML: {cookie_name}")
            except Exception as sc_exc:
                print(f"FORWARDER — Set-Cookie parse error: {sc_exc}")

        # Also set the auto-login session cookie on the browser so subsequent
        # asset/API requests are authenticated (server-side cookies don't reach the browser otherwise)
        if upstream_cookies.get('session_id') and 'session_id' not in response.cookies:
            response.cookies['session_id'] = upstream_cookies['session_id']
            response.cookies['session_id']['path'] = '/'
            response.cookies['session_id']['samesite'] = 'Lax'
            print(f"FORWARDER — set browser session_id cookie from auto-login")

        # Wrap HTML responses in admin template for embedded display (generic, all endpoints)
        # Skip API calls, static assets, and non-HTML responses
        upstream_path = getattr(request, '_passthrough_upstream_path', '')
        is_page_load = not any(upstream_path.endswith(ext) for ext in ['.js', '.css', '.png', '.jpg', '.json', '.woff', '.woff2'])
        is_page_load = is_page_load and '/api/' not in upstream_path and '/static/' not in upstream_path
        if is_page_load and resp.status_code == 200:
            print(f"[FORWARDER] Wrapping passthrough HTML in admin template")
            response = _wrap_in_admin_template(request, response, trigger or 'passthrough', endpoint)

        print("FORWARDER SUCCESS — RESPONSE SENT TO BROWSER")
        print("=" * 120 + "\n")

        return response

    except Exception as e:
        # PRINT THE TRUTH — NEVER LIE
        tb = traceback.format_exc()
        print("\n" + "!"*120)
        print("FORWARDER FAILED — FULL TRUTH BELOW")
        print(f"EXCEPTION TYPE: {type(e).__name__}")
        print(f"EXCEPTION     : {e}")
        print(f"TARGET URL    : {target_url if 'target_url' in locals() else 'UNKNOWN'}")
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

        return HttpResponse(error_html, status=502)
