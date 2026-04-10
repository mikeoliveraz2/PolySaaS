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
        raw_html = fetch_upstream_index_html(
            request, endpoint.endpoint_url, "/", handler=self
        )
        if raw_html and not raw_html.startswith("REDIRECT:"):
            proxy_prefix = "/pt/admin/mattermost"
            _static_attr = re.compile(
                r'(src|href)=(["\'])(/static/[^"\']*)', re.IGNORECASE
            )

            def _rewrite_static_attrs(fragment):
                if not fragment:
                    return fragment
                return _static_attr.sub(
                    lambda m2: (
                        f"{m2.group(1)}={m2.group(2)}{proxy_prefix}{m2.group(3)}{m2.group(2)}"
                    ),
                    fragment,
                )

            m = re.search(
                r"<head[^>]*>(.*?)</head>",
                raw_html,
                re.DOTALL | re.IGNORECASE,
            )
            if m:
                display_head_inner = _rewrite_static_attrs(m.group(1).strip())
            m_body = re.search(
                r"<body[^>]*>(.*?)</body>",
                raw_html,
                re.DOTALL | re.IGNORECASE,
            )
            if m_body:
                display_body_inner = _rewrite_static_attrs(m_body.group(1).strip())

        # Full shim: token + webpack + fetch/XHR/WebSocket (display shell had only the first half → spinner).
        proxy_prefix = "/pt/admin/mattermost"
        _origin = endpoint.endpoint_url.rstrip("/")
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

        html_str = re.sub(
            r'(src|href)=(["\'])([^"\']*?[\w.-]+\.(js|css|png|jpg|jpeg|gif|svg|woff2?|ttf|eot|json|map))',
            lambda m: f'{m.group(1)}={m.group(2)}{proxy_prefix}{m.group(3)}{m.group(2)}',
            html_str,
            flags=re.IGNORECASE,
        )

        html_str = re.sub(
            r'(src|href)=(["\'])(/static/[^"\']*)',
            lambda m: f'{m.group(1)}={m.group(2)}{proxy_prefix}{m.group(3)}{m.group(2)}',
            html_str,
            flags=re.IGNORECASE,
        )

        html_str = self._inject_client_shim(
            html_str, base_origin, request, proxy_prefix
        )

        return html_str, None

    def get_upstream_cookies(self, request):
        """
        Provide session cookies for SSO/auto-login to Mattermost.
        Mattermost primarily uses MMAUTHTOKEN header/cookie.
        """
        try:
            from dose.models import TenantApp
            from dose.utils import get_current_tenant
            import requests as _req

            tenant = get_current_tenant(request)
            if not tenant:
                return {}

            ta = TenantApp.objects.filter(
                tenant=tenant, app_name='mattermost', status='active'
            ).first()

            if not ta or not ta.extra_config:
                return {}

            # Try cached MMAUTHTOKEN first (check multiple possible key names)
            token = (ta.extra_config.get('mmauthtoken') or 
                     ta.extra_config.get('mm_session_token') or
                     ta.extra_config.get('mm_token'))
            token_time = (ta.extra_config.get('mmauthtoken_time') or 
                          ta.extra_config.get('mm_session_token_time', 0))

            if token and (time.time() - token_time < 3600):
                logger.info("[MattermostPassthroughHandler] Using cached token: %s...", token[:8] if token else 'None')
                return {'MMAUTHTOKEN': token}

            # Refresh session if needed (check multiple possible key names)
            password = (ta.extra_config.get('mattermost_password') or 
                        ta.extra_config.get('mm_password') or
                        ta.extra_config.get('password'))
            if not password:
                logger.warning("[MattermostPassthroughHandler] No password available in extra_config")
                return {}

            login_id = (ta.extra_config.get('mattermost_login_id') or 
                        ta.extra_config.get('mm_login_id') or
                        request.user.email)

            resp = _req.post(
                'http://localhost:8065/api/v4/users/login',
                json={'login_id': login_id, 'password': password},
                timeout=10,
            )

            if resp.status_code == 200:
                token = resp.headers.get('Token')
                if token:
                    # Save with both key names for compatibility
                    ta.extra_config['mmauthtoken'] = token
                    ta.extra_config['mmauthtoken_time'] = time.time()
                    ta.extra_config['mm_session_token'] = token
                    ta.extra_config['mm_session_token_time'] = time.time()
                    ta.save(update_fields=['extra_config'])
                    logger.info("[MattermostPassthroughHandler] MMAUTHTOKEN refreshed: %s...", token[:8])
                    return {'MMAUTHTOKEN': token}

        except Exception as exc:
            logger.warning("[MattermostPassthroughHandler] get_upstream_cookies failed: %s", exc)

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
        if (typeof input === 'string') {{
            input = toProxy(input);
        }} else if (typeof Request !== 'undefined' && input instanceof Request) {{
            var u = toProxy(input.url);
            if (u !== input.url) input = new Request(u, input);
        }}
        return _f.call(this, input, init);
    }};

    var _xo = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {{
        var rest = Array.prototype.slice.call(arguments, 2);
        return _xo.apply(this, [method, toProxy(url)].concat(rest));
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
