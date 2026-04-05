# dose/passthrough/forwarding.py — FINAL — PRINTS EVERYTHING — EXCEPTIONS SHOW TRUTH
import logging
import traceback
import requests
import json
import time
from django.http import HttpResponse
from dose.polysniffer.models import TrafficLog

logger = logging.getLogger(__name__)

_SKIP_META = frozenset({"HTTP_HOST", "HTTP_CONTENT_LENGTH", "CONTENT_LENGTH", "HTTP_COOKIE"})


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


def fetch_upstream_index_html(request, endpoint_url, upstream_subpath="/", handler=None):
    """
    GET upstream HTML mimicking a real browser request.
    Injects any app-specific cookies (e.g. MMAUTHTOKEN) via handler.get_upstream_cookies().
    If the upstream returns a 3xx redirect the redirect target URL is returned as a string
    prefixed with 'REDIRECT:' so the caller can pass it straight through to the browser.
    """
    clean = upstream_subpath or "/"
    if not clean.startswith("/"):
        clean = "/" + clean
    target_url = endpoint_url.rstrip("/") + clean

    # Merge browser cookies with any app-specific cookies the handler wants to inject.
    # Browser cookies take priority — after a manual login the browser has the fresh
    # session token; the server's cached token may be stale.
    upstream_cookies = dict(request.COOKIES)
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
    for _hop in range(5):
        try:
            resp = requests.get(
                _current_url,
                headers=_outbound_headers_from_request(request),
                cookies=upstream_cookies,
                allow_redirects=False,
                timeout=60,
            )
        except Exception as e:
            logger.warning("fetch_upstream_index_html %s failed: %s", _current_url, e)
            return ""

        if not (resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308)):
            break   # got actual content

        location = resp.headers.get("Location", "")
        if not location:
            break
        # Make relative location absolute
        if not location.startswith(("http://", "https://")):
            location = _origin + (location if location.startswith('/') else '/' + location)
        # Only follow if same origin; hand cross-origin redirects back to the caller
        loc_origin = f"{_up(location).scheme}://{_up(location).netloc}"
        if loc_origin != _origin:
            logger.info("fetch_upstream_index_html cross-origin redirect -> %s", location)
            return f"REDIRECT:{resp.status_code}:{location}"
        logger.info("fetch_upstream_index_html following %s -> %s", _current_url, location)
        _current_url = location
    else:
        # Exhausted redirect hops
        logger.warning("fetch_upstream_index_html: too many redirects from %s", target_url)
        return ""

    if resp.status_code != 200:
        logger.warning(
            "fetch_upstream_index_html %s -> status %s", target_url, resp.status_code
        )
        return ""

    # ── PolySniffer Capture (Initial HTML) ─────────────────────────────
    try:
        from dose.polysniffer.models import TrafficLog
        from django.contrib.auth.models import AnonymousUser
        from django.db import connection
        
        capture_user = request.user if (request.user and not isinstance(request.user, AnonymousUser)) else None
        
        app_name = "unknown"
        if handler:
            app_name = handler.__class__.__name__.lower().replace("passthroughhandler", "")

        # Ensure we are in the TENANT schema
        tenant = getattr(request, "tenant", None)
        if tenant:
            with connection.cursor() as cur:
                cur.execute(f"SET search_path TO {tenant.schema_name}, public;")

        TrafficLog.objects.create(
            method="GET",
            url=target_url,
            path=upstream_subpath,
            headers=_outbound_headers_from_request(request),
            cookies=upstream_cookies,
            query_params=dict(request.GET),
            body="",
            status_code=resp.status_code,
            response_headers=dict(resp.headers),
            response_body=resp.content.decode("utf-8", errors="ignore"),
            response_size=len(resp.content),
            endpoint_name=app_name,
            user=capture_user,
            duration_ms=0,
        )
        print(f"POLY SNIFFER — Captured Initial HTML for {app_name} in schema {tenant.schema_name if tenant else 'public'}")
    except Exception as ps_exc:
        print(f"POLY SNIFFER — Initial HTML capture failed: {ps_exc}")
    # ───────────────────────────────────────────────────────────────────

    return resp.content.decode("utf-8", errors="ignore")


def forward_request_standardized(request, endpoint_url, handler=None):
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
        full_path = request.get_full_path()

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
            target_url = endpoint_url.rstrip("/") + clean
            print(f"PASSTHROUGH -> {full_path} -> {target_url}")
        else:
            upstream_path = "/"
            target_url = endpoint_url
            print(f"PASSTHROUGH -> USING ENDPOINT ROOT: {target_url}")

        print(f"SENDING REQUEST TO -> {target_url}")

        # Never forward the browser's Host (e.g. localhost:8000); upstream must see its own host.
        outbound_headers = _outbound_headers_from_request(request)

        # === FIX FOR BLANK ODOO SCREEN - PROPER PROXY HEADERS ===
        if "odoo" in target_url.lower() or (handler and "odoo" in handler.__class__.__name__.lower()):
            outbound_headers['Host'] = 'localhost:8069'
            outbound_headers['X-Forwarded-For'] = request.META.get('REMOTE_ADDR', '')
            outbound_headers['X-Forwarded-Proto'] = 'http' if 'localhost' in request.get_host() else 'https'
            outbound_headers['X-Forwarded-Host'] = request.get_host()
            outbound_headers['X-Forwarded-Port'] = '8069'
            # Remove any conflicting headers that break Odoo assets
            outbound_headers.pop('Referer', None)

        # Merge browser cookies with any app-specific cookies the handler wants to inject.
        # Browser cookies take priority — after a manual login the browser has the fresh
        # session token; the server's cached token may be stale.
        upstream_cookies = dict(request.COOKIES)
        if handler and hasattr(handler, "get_upstream_cookies"):
            try:
                extra = handler.get_upstream_cookies(request) or {}
                for k, v in extra.items():
                    if k not in upstream_cookies:   # don't overwrite what the browser already has
                        upstream_cookies[k] = v
            except Exception as exc:
                logger.warning("get_upstream_cookies failed: %s", exc)

        # Debug: for login requests, print exactly what is going to Mattermost
        if "login" in target_url.lower():
            print("=== LOGIN FORWARD DEBUG ===")
            print(f"TARGET            : {target_url}")
            print(f"Cookie header sent: {'Cookie' in outbound_headers}")
            print(f"Cookies param     : { {k: v[:8]+'...' if v and len(v)>8 else v for k,v in upstream_cookies.items()} }")
            print(f"Body preview      : {request.body[:200] if request.body else '(empty)'}")
            print("===========================")

        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=outbound_headers,
            data=request.body,
            cookies=upstream_cookies,
            allow_redirects=False,   # pass 302s straight through to browser
            stream=False,
            timeout=60,
        )

        if "odoo" in target_url.lower() or (handler and "odoo" in handler.__class__.__name__.lower()):
            print("=== ODOO FIX #4 DEBUG ===")
            print("Status:", resp.status_code)
            print("Content-Type:", resp.headers.get('content-type'))
            print("Content-Length:", len(resp.content) if resp.content else 0)
            print("Body preview (first 600 chars):")
            print(repr(resp.content[:600]) if resp.content else "EMPTY BODY")
            print("================================")

            # === DYNAMIC WIDTH FIX - Sidebar-aware adaptive display ===
            if b'</head>' in resp.content:
                # Get real sidebar width from PolySaaS (usually 260px when open)
                sidebar_width = 260
                
                inject = f'''
                <style id="polysaas-dynamic-width">
                    html, body, .o_web_client, #wrapwrap, #app, .app-content {{
                        width: calc(100vw - {sidebar_width}px) !important;
                        max-width: calc(100vw - {sidebar_width}px) !important;
                        margin-left: auto !important;
                        margin-right: auto !important;
                    }}
                    
                    /* When sidebar collapses, expand fully */
                    @media (max-width: 1024px) {{
                        .o_web_client, .app-content {{
                            width: 100vw !important;
                        }}
                    }}
                    
                    /* Force Odoo to respect available space */
                    .o_form_view, .o_list_view, .o_kanban_view {{
                        width: 100% !important;
                    }}
                </style>
                '''.encode('utf-8')
                
                # We need to be careful about bytes vs string here.
                # resp.content is bytes.
                resp._content = resp.content.replace(b'</head>', inject + b'</head>')

        print(f"EXTERNAL SERVICE RESPONDED -> STATUS: {resp.status_code}")
        print(f"CONTENT LENGTH: {len(resp.content)} bytes")
        preview_bytes = resp.content[:500] if resp.content else b""
        print(f"CONTENT PREVIEW: {preview_bytes.decode('utf-8', errors='ignore')}")

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

            TrafficLog.objects.create(
                method=request.method,
                url=target_url,
                path=upstream_path,
                headers=dict(request.headers),
                cookies=dict(request.COOKIES),
                query_params=dict(request.GET),
                body=request.body.decode("utf-8", errors="ignore") if request.body else "",
                status_code=resp.status_code,
                response_headers=dict(resp.headers),
                response_body=resp.content.decode("utf-8", errors="ignore") if resp.content else "",
                response_size=len(resp.content),
                endpoint_name=app_name,
                user=capture_user,
                duration_ms=0,
            )
            print(f"POLY SNIFFER — Captured {request.method} {upstream_path} for {app_name} in schema {tenant.schema_name if tenant else 'public'}")
        except Exception as ps_exc:
            print(f"POLY SNIFFER — Capture failed (non-blocking): {ps_exc}")
        # ───────────────────────────────────────────────────────────────────

        # Pass redirects straight through — make relative Locations absolute so browser hits upstream
        if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location", "/")
            if location and not location.startswith(("http://", "https://")):
                from urllib.parse import urlparse as _up
                p = _up(target_url)
                location = f"{p.scheme}://{p.netloc}{location if location.startswith('/') else '/' + location}"
            print(f"FORWARDER — upstream {resp.status_code} redirect to {location}, passing through")
            redirect_response = HttpResponse(status=resp.status_code)
            redirect_response["Location"] = location
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
                "Content-Disposition",
                "Content-Language",
                "X-Requested-With",
                "Token",       # Mattermost login response — SPA reads this to get the session token
            )
            if body_rewritten:
                _copy_headers = tuple(h for h in _copy_headers if h != "ETag")
            for hk in _copy_headers:
                if hk in resp.headers:
                    response[hk] = resp.headers[hk]

            # Forward Set-Cookie headers from upstream so the browser receives MMUSERID and MMCSRF
            # after Mattermost login.  Without MMCSRF the SPA cannot set X-CSRF-Token on POSTs.
            # Strip HttpOnly so JS can read MMAUTHTOKEN; strip Domain so cookies bind to PolySaaS host.
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
                        # intentionally omit httponly and domain
                        print(f"FORWARDER — forwarding Set-Cookie: {cookie_name}=<redacted>")
                except Exception as sc_exc:
                    print(f"FORWARDER — Set-Cookie parse error: {sc_exc}")
            response["X-Frame-Options"] = "ALLOWALL"
            print("FORWARDER SUCCESS — BINARY/TEXT PASSTHROUGH (non-HTML)")
            print("=" * 120 + "\n")
            return response

        content = resp.content.decode("utf-8", errors="ignore")

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