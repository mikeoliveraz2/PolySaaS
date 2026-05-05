# Auto-generated PassthroughHandler for Mattermost
# Generated from PolySniffer analysis of http://localhost:8065
# 
# This handler provides:
# - SSO via get_upstream_cookies()
# - URL rewriting for static assets and API calls
# - Client-side shim for dynamic requests (fetch, XHR, WebSocket)
# - Strict enforcement of /pt/admin/mattermost/ prefix

import json
import logging
import re
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class MattermostPassthroughHandler:
    """
    Passthrough handler for Mattermost.
    Generated from PolySniffer captures - do not hand-edit.
    Regenerate from fresh captures if behavior changes.
    """

    def _get_endpoint_url(self):
        """Get the actual Mattermost endpoint URL from the database config."""
        try:
            from dose.models import PassThroughEndpoint
            ep = PassThroughEndpoint.objects.filter(
                trigger_path='mattermost', is_enabled=True
            ).first()
            if ep and ep.endpoint_url:
                return ep.endpoint_url.rstrip('/')
        except Exception:
            pass
        # Fallback to settings or localhost
        try:
            from django.conf import settings
            return getattr(settings, 'MATTERMOST_URL', 'http://localhost:8065').rstrip('/')
        except Exception:
            return 'http://localhost:8065'

    def should_delegate_pt_admin_core(self, request, path_info: str) -> bool:
        """Static bundle URLs are served by mattermost_static_proxy in URLconf, not PT core."""
        return path_info.startswith("/pt/admin/mattermost/static/")

    def try_root_display_shell_response(self, request, endpoint, url_trigger_segment):
        """
        GET /pt/admin/<trigger>/ root: display shell; fetch upstream HTML, extract <head> and
        <body> inner HTML; rewrite href|src starting with /static/ in both to use
        /pt/admin/mattermost/static/... (mattermost_static_proxy).
        """
        if request.method != "GET":
            return None
        seg = (
            url_trigger_segment.strip("/").lower().split("/")[-1].replace("-", "_")
        )
        if request.path_info.rstrip("/") != f"/pt/admin/{seg}":
            return None
        from django.shortcuts import render
        from django.utils.safestring import mark_safe

        from dose.passthrough.forwarding import fetch_upstream_index_html

        display_head_inner = ""
        display_body_inner = ""
        # Use _get_endpoint_url to get the actual configured URL, not the fallback
        actual_endpoint_url = self._get_endpoint_url() or endpoint.endpoint_url
        print(f"[MATTERMOST_DISPLAY] Endpoint URL: {actual_endpoint_url}")
        upstream_result = fetch_upstream_index_html(
            request, actual_endpoint_url, "/", handler=self
        )
        print(f"[MATTERMOST_DISPLAY] upstream_result type: {type(upstream_result).__name__}")
        
        # fetch_upstream_index_html returns HttpResponse on success, str sentinel on redirect, "" on error
        raw_html = ""
        if hasattr(upstream_result, 'content'):
            try:
                raw_html = upstream_result.content.decode('utf-8')
                print(f"[MATTERMOST_DISPLAY] Got HttpResponse, content length: {len(upstream_result.content)}")
            except Exception as e:
                print(f"[MATTERMOST_DISPLAY] Decode error: {e}")
                raw_html = upstream_result.content.decode('utf-8', errors='replace')
        elif isinstance(upstream_result, str):
            raw_html = upstream_result
            print(f"[MATTERMOST_DISPLAY] Got string, length: {len(raw_html)}, starts with: {raw_html[:50] if raw_html else 'EMPTY'}")

        print(f"[MATTERMOST_DISPLAY] raw_html length: {len(raw_html)}, has head: {'<head' in raw_html}, has body: {'<body' in raw_html}")
        
        # fetch_upstream_index_html does NOT call process_html_response — we must do it here
        processed_html = raw_html
        if raw_html and not raw_html.startswith("REDIRECT:"):
            try:
                processed, _ = self.process_html_response(
                    raw_html, request, endpoint_url=actual_endpoint_url
                )
                if processed:
                    processed_html = processed
                    print(f"[MATTERMOST_DISPLAY] process_html_response applied, URLs rewritten")
            except Exception as e:
                print(f"[MATTERMOST_DISPLAY] process_html_response failed: {e}")
        
        if processed_html and not processed_html.startswith("REDIRECT:"):
            m = re.search(
                r"<head[^>]*>(.*?)</head>",
                processed_html,
                re.DOTALL | re.IGNORECASE,
            )
            if m:
                display_head_inner = m.group(1).strip()
                print(f"[MATTERMOST_DISPLAY] Extracted head, length: {len(display_head_inner)}")
            else:
                print("[MATTERMOST_DISPLAY] No <head> found in processed_html")
            m_body = re.search(
                r"<body[^>]*>(.*?)</body>",
                processed_html,
                re.DOTALL | re.IGNORECASE,
            )
            if m_body:
                display_body_inner = m_body.group(1).strip()
                print(f"[MATTERMOST_DISPLAY] Extracted body, length: {len(display_body_inner)}")
            else:
                print("[MATTERMOST_DISPLAY] No <body> found in processed_html")
        else:
            print(f"[MATTERMOST_DISPLAY] processed_html empty or redirect: {processed_html[:100] if processed_html else 'EMPTY'}")

        # Full shim: token + webpack + fetch/XHR/WebSocket (display shell had only the first half → spinner).
        proxy_prefix = "/pt/admin/mattermost"
        _origin = actual_endpoint_url.rstrip("/")
        _p = urlparse(_origin)
        base_origin = f"{_p.scheme}://{_p.netloc}"
        shim_html = self._mattermost_display_shim_html(
            request, proxy_prefix, base_origin
        )
        if shim_html:
            display_head_inner = shim_html + display_head_inner

        response = render(
            request,
            "admin/display.html",
            {
                "display_head_inner": mark_safe(display_head_inner)
                if display_head_inner
                else "",
                "display_body_inner": mark_safe(display_body_inner)
                if display_body_inner
                else "",
                "display_shell_footer": "Mattermost passthrough — static assets use /pt/admin/mattermost/static/.",
                "display_enable_odoo_body_scope": False,
            },
        )
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response

    def process_html_response(self, html_str, request, endpoint_url=None, *args, **kwargs):
        logger.info("[MattermostPassthroughHandler] Processing HTML response")

        if not endpoint_url:
            return html_str, None

        origin = endpoint_url.rstrip("/")
        parsed = urlparse(origin)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"
        proxy_prefix = "/pt/admin/mattermost"

        html_str = self._strip_base_tags(html_str)
        html_str = self._strip_meta_redirects(html_str)
        html_str = self._strip_csp(html_str)

        # Rewrite file paths with extensions (capture query param as part of group 3, not separate)
        html_str = re.sub(
            r'(src|href)=(["\'])([^"\']*?[\w.-]+\.(js|css|png|jpg|jpeg|gif|svg|woff2?|ttf|eot|json|map)(?:\?[^"\']*)?)',
            lambda m: f'{m.group(1)}={m.group(2)}{proxy_prefix}{m.group(3)}{m.group(2)}',
            html_str,
            flags=re.IGNORECASE,
        )

        html_str = re.sub(
            r'(src|href)=(["\'])(/static/[^"\']*(?:\?[^"\']*)?)',
            lambda m: f'{m.group(1)}={m.group(2)}{proxy_prefix}{m.group(3)}{m.group(2)}',
            html_str,
            flags=re.IGNORECASE,
        )

        # Rewrite absolute upstream-origin URLs (e.g. https://polysaas-mattermost.onrender.com/static/...)
        _abs_static = re.escape(base_origin) + r'/static/'
        html_str = re.sub(
            r'(src|href)=(["\'])' + _abs_static + r'([^"\']*)',
            lambda m: f'{m.group(1)}={m.group(2)}{proxy_prefix}/static/{m.group(3)}{m.group(2)}',
            html_str,
            flags=re.IGNORECASE,
        )

        html_str = self._inject_client_shim(
            html_str, base_origin, request, proxy_prefix
        )

        return html_str, None

    def _get_tenantapp_extra_config(self):
        """Query TenantApp extra_config from public schema using raw SQL to avoid schema issues."""
        import json
        from django.db import connection
        with connection.cursor() as cur:
            cur.execute("SET search_path TO public,pg_catalog")
            cur.execute(
                """SELECT extra_config FROM dose_tenantapp
                   WHERE app_name = 'mattermost' AND status = 'active'
                   LIMIT 1""",
            )
            row = cur.fetchone()
            if row and row[0]:
                cfg = row[0]
                # PostgreSQL JSONField may return dict or JSON string
                if isinstance(cfg, str):
                    return json.loads(cfg)
                return cfg
        return None

    def _save_tenantapp_token(self, token):
        """Save refreshed token to public schema TenantApp using raw SQL."""
        import json
        import time
        from django.db import connection
        with connection.cursor() as cur:
            cur.execute("SET search_path TO public,pg_catalog")
            # Build updated extra_config with new token
            extra = self._get_tenantapp_extra_config() or {}
            extra['mmauthtoken'] = token
            extra['mmauthtoken_time'] = time.time()
            extra['mm_session_token'] = token
            extra['mm_session_token_time'] = time.time()
            cur.execute(
                """UPDATE dose_tenantapp SET extra_config = %s
                   WHERE app_name = 'mattermost' AND status = 'active'""",
                [json.dumps(extra)],
            )

    def get_upstream_cookies(self, request):
        """
        Provide session cookies for SSO/auto-login to Mattermost.
        Mattermost primarily uses MMAUTHTOKEN header/cookie.
        """
        try:
            from dose.utils import get_current_tenant
            import requests as _req

            tenant = get_current_tenant(request)
            print(f"[MM_AUTH] tenant: {tenant}")
            if not tenant:
                return {}

            extra_config = self._get_tenantapp_extra_config()
            print(f"[MM_AUTH] extra_config found: {extra_config is not None}")

            if not extra_config:
                print("[MM_AUTH] No extra_config for mattermost TenantApp")
                return {}

            # Try cached MMAUTHTOKEN first
            token = (extra_config.get('mmauthtoken') or 
                     extra_config.get('mm_session_token') or
                     extra_config.get('mm_token'))
            token_time = (extra_config.get('mmauthtoken_time') or 
                          extra_config.get('mm_session_token_time', 0))

            if token and (time.time() - token_time < 3600):
                logger.info("[MattermostPassthroughHandler] Using cached token: %s...", token[:8] if token else 'None')
                return {'MMAUTHTOKEN': token}

            # Refresh session if needed
            password = (extra_config.get('mattermost_password') or 
                        extra_config.get('mm_password') or
                        extra_config.get('password'))
            print(f"[MM_AUTH] password present: {bool(password)}")
            if not password:
                logger.warning("[MattermostPassthroughHandler] No password available in extra_config")
                return {}

            login_id = (extra_config.get('mattermost_login_id') or 
                        extra_config.get('mm_login_id') or
                        request.user.email)
            print(f"[MM_AUTH] login_id: {login_id}")

            mm_origin = self._get_endpoint_url()
            print(f"[MM_AUTH] mm_origin: {mm_origin}")
            resp = _req.post(
                f'{mm_origin}/api/v4/users/login',
                json={'login_id': login_id, 'password': password},
                timeout=10,
            )
            print(f"[MM_AUTH] login response status: {resp.status_code}")

            if resp.status_code == 200:
                token = resp.headers.get('Token')
                print(f"[MM_AUTH] Token header present: {bool(token)}")
                if token:
                    self._save_tenantapp_token(token)
                    logger.info("[MattermostPassthroughHandler] MMAUTHTOKEN refreshed: %s...", token[:8])
                    return {'MMAUTHTOKEN': token}

        except Exception as exc:
            logger.warning("[MattermostPassthroughHandler] get_upstream_cookies failed: %s", exc)
            print(f"[MM_AUTH] EXCEPTION: {exc}")

        return {}

    def _strip_base_tags(self, html):
        return re.sub(r"<base\b[^>]*>", "", html, flags=re.IGNORECASE)

    def _strip_meta_redirects(self, html):
        return re.sub(r'<meta\s+http-equiv\s*=\s*["\']refresh["\'][^>]*>', "", html, flags=re.IGNORECASE)

    def _strip_csp(self, html):
        return re.sub(r'<meta\s+http-equiv\s*=\s*["\']Content-Security-Policy["\'][^>]*>', "", html, flags=re.IGNORECASE)

    def _mattermost_display_shim_html(
        self, request, proxy_prefix: str, base_origin: str
    ) -> str:
        """
        Full client shim for Mattermost in PolySaaS: MMAUTHTOKEN, webpack public path,
        fetch/XHR/WebSocket → proxy, attribute/prototype patching (matches generated handler).
        Display shell must include network patches or API/WS stay on the admin origin → spinner.
        """
        token = ""
        try:
            cookies = self.get_upstream_cookies(request) or {}
            token = cookies.get("MMAUTHTOKEN") or ""
        except Exception as exc:
            logger.warning("[MattermostPassthroughHandler] Token lookup failed: %s", exc)

        token_js = json.dumps(token)
        proxy_js = json.dumps(proxy_prefix)
        base_js = json.dumps(base_origin.rstrip("/"))

        return f"""
<script data-polysaas-mattermost-shim="1">
(function() {{
    var B = {base_js};
    var PROXY = {proxy_js};
    var O = window.location.origin;
    var MMAUTHTOKEN = {token_js};

    var PS_PREFIXES = ['/static/admin/', '/static/img/', '/admin/', '/dose/', '/media/', '/accounts/', '/pt/', '/favicon'];
    function isPolySaaSPath(s) {{
        for (var i = 0; i < PS_PREFIXES.length; i++) {{
            if (s.startsWith(PS_PREFIXES[i])) return true;
        }}
        return false;
    }}

    function toProxy(s) {{
        if (typeof s !== 'string') return s;
        if (!s || s.startsWith('data:') || s.startsWith('blob:')) return s;
        if (s.startsWith(B)) {{
            var tail = s.slice(B.length);
            if (!tail.startsWith('/')) tail = '/' + tail;
            return PROXY + tail;
        }}
        if (s.startsWith(O + '/')) s = s.slice(O.length);
        else if (s.startsWith('http:') || s.startsWith('https:') || s.indexOf('//') === 0) return s;
        if (s.charAt(0) !== '/') return s;
        if (isPolySaaSPath(s)) return s;
        return PROXY + s;
    }}

    if (MMAUTHTOKEN) {{
        try {{
            localStorage.setItem('MMAUTHTOKEN', MMAUTHTOKEN);
            document.cookie = 'MMAUTHTOKEN=' + MMAUTHTOKEN + '; path=/; max-age=3600';
            window.MMAUTHTOKEN = MMAUTHTOKEN;
            console.log('[PolySaaS Mattermost] MMAUTHTOKEN injected');
        }} catch (e) {{
            console.warn('[PolySaaS Mattermost] Token injection failed:', e);
        }}
    }}

    window.__webpack_public_path__ = PROXY + '/static/';

    var _f = window.fetch;
    window.fetch = function(input, init) {{
        var original = input;
        if (typeof input === 'string') {{
            input = toProxy(input);
        }} else if (typeof Request !== 'undefined' && input instanceof Request) {{
            var u = toProxy(input.url);
            if (u !== input.url) input = new Request(u, input);
        }}
        if (original !== input) console.log('[PolySaaS MM] fetch:', original, '->', input);
        return _f.call(this, input, init);
    }};

    var _xo = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {{
        var proxied = toProxy(url);
        if (url !== proxied) console.log('[PolySaaS MM] XHR:', method, url, '->', proxied);
        var rest = Array.prototype.slice.call(arguments, 2);
        return _xo.apply(this, [method, proxied].concat(rest));
    }};

    var _WS = WebSocket;
    window.WebSocket = function(url, protocols) {{
        if (typeof url === 'string') {{
            try {{
                var u = new URL(url, location.href);
                u.hostname = location.hostname;
                u.port = location.port || '';
                u.protocol = (location.protocol === 'https:') ? 'wss:' : 'ws:';
                if (!u.pathname.startsWith('/pt/')) {{
                    u.pathname = PROXY + u.pathname;
                }}
                url = u.toString();
                console.log('[PolySaaS Mattermost] WebSocket via proxy:', url);
            }} catch (e) {{ console.warn('[PolySaaS Mattermost] WebSocket rewrite:', e); }}
        }}
        if (protocols !== undefined) return new _WS(url, protocols);
        return new _WS(url);
    }};
    if (_WS.CONNECTING !== undefined) window.WebSocket.CONNECTING = _WS.CONNECTING;
    if (_WS.OPEN !== undefined) window.WebSocket.OPEN = _WS.OPEN;
    if (_WS.CLOSING !== undefined) window.WebSocket.CLOSING = _WS.CLOSING;
    if (_WS.CLOSED !== undefined) window.WebSocket.CLOSED = _WS.CLOSED;

    function patchProp(proto, prop) {{
        var d = Object.getOwnPropertyDescriptor(proto, prop);
        if (!d || !d.set) return;
        Object.defineProperty(proto, prop, {{
            get: d.get,
            set: function(v) {{
                if (typeof v === 'string') v = toProxy(v);
                d.set.call(this, v);
            }},
            configurable: true, enumerable: true
        }});
    }}
    patchProp(HTMLScriptElement.prototype, 'src');
    patchProp(HTMLLinkElement.prototype, 'href');
    patchProp(HTMLImageElement.prototype, 'src');

    var _setAttr = Element.prototype.setAttribute;
    Element.prototype.setAttribute = function(name, value) {{
        if (typeof value === 'string') {{
            var ln = name.toLowerCase();
            if ((ln === 'src' || ln === 'href') &&
                (this instanceof HTMLScriptElement || this instanceof HTMLLinkElement || this instanceof HTMLImageElement)) {{
                value = toProxy(value);
            }}
        }}
        return _setAttr.call(this, name, value);
    }};

    // Monitor script errors from Mattermost bundles
    window.addEventListener('error', function(e) {{
        console.error('[PolySaaS MM] Global error:', e.message, 'at', e.filename, ':', e.lineno);
    }});
    window.addEventListener('unhandledrejection', function(e) {{
        console.error('[PolySaaS MM] Unhandled promise rejection:', e.reason);
    }});
    // Log when scripts are loaded
    var _origAppend = HTMLHeadElement.prototype.appendChild;
    HTMLHeadElement.prototype.appendChild = function(node) {{
        if (node.tagName === 'SCRIPT') console.log('[PolySaaS MM] Script appended:', node.src || '(inline)');
        return _origAppend.call(this, node);
    }};
    console.log('[PolySaaS Mattermost] Full shim loaded, proxy=', PROXY);
}})();
</script>
"""

    def _inject_client_shim(self, html, base_origin, request, proxy_prefix):
        """Inject full Mattermost shim first in <head>."""
        shim = self._mattermost_display_shim_html(
            request, proxy_prefix, base_origin
        )

        if re.search(r"<head\b", html, re.IGNORECASE):
            return re.sub(
                r"(<head[^>]*>)",
                lambda m: m.group(1) + shim,
                html,
                count=1,
                flags=re.IGNORECASE,
            )
        return shim + html
