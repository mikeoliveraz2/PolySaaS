# Auto-generated PassthroughHandler for mattermost
# Generated from PolySniffer analysis of http://localhost:8065
# 
# This handler provides:
# - SSO/auto-login via get_upstream_cookies()
# - URL rewriting and shim injection via process_html_response()
# - All traffic flows through /pt/admin/mattermost/ for PolySniffer capture

import json
import logging
import re
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class MattermostPassthroughHandler:
    """
    Passthrough handler for mattermost.
    Generated from PolySniffer captures - do not hand-edit.
    Regenerate from fresh captures if behavior changes.
    """

    def process_html_response(self, html_str, request, endpoint_url=None, *args, **kwargs):
        """
        Process upstream HTML for embedded display in PolySaaS admin.
        - Strips problematic tags (<base>, meta redirects, CSP)
        - Injects client-side shim for URL rewriting
        - Rewrites asset URLs to go through proxy
        """
        logger.info("[MattermostPassthroughHandler] Processing HTML response")

        if not endpoint_url:
            return html_str, None

        origin = endpoint_url.rstrip("/")
        parsed = urlparse(origin)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"

        # Strip tags that break embedded display
        html_str = self._strip_base_tags(html_str)
        html_str = self._strip_meta_redirects(html_str)
        html_str = self._strip_csp(html_str)

        # Inject client-side shim
        html_str = self._inject_client_shim(html_str, base_origin, request)

        return html_str, None

    def get_upstream_cookies(self, request):
        """
        Provide session cookies for SSO/auto-login.
        Uses credentials from TenantApp.extra_config to obtain fresh session.
        """
        try:
            from dose.models import TenantApp
            from dose.utils import get_current_tenant
            import requests as _req

            tenant = get_current_tenant(request)
            if not tenant:
                return {}

            ta = TenantApp.objects.filter(
                tenant=tenant, app_name='mattermost', status='active',
            ).first()
            if not ta or not ta.extra_config:
                return {}

            # Check for cached session token (less than 1 hour old)
            session_token = ta.extra_config.get('mattermost_session_token')
            session_token_time = ta.extra_config.get('mattermost_session_token_time', 0)
            if session_token and (time.time() - session_token_time < 3600):
                return {'sessionid': session_token}

            # Expired or missing - perform fresh login
            logger.info("[MattermostPassthroughHandler] Session token expired or missing - refreshing")
            
            password = ta.extra_config.get('mattermost_password') or ta.extra_config.get('password')
            if not password:
                logger.warning("[MattermostPassthroughHandler] No password in extra_config")
                return {}

            login_id = ta.extra_config.get('mattermost_login_id') or ta.extra_config.get('login_id') or request.user.email
            
            # Perform login
            resp = _req.post(
                'http://localhost:8065/api/v4/users/login',
                json={'login_id': login_id, 'password': password},
                timeout=10,
            )
            
            if resp.status_code == 200:
                # Extract session token from response header or cookies
                token = resp.headers.get('Token') or resp.cookies.get('sessionid')
                if token:
                    ta.extra_config['mattermost_session_token'] = token
                    ta.extra_config['mattermost_session_token_time'] = time.time()
                    ta.save(update_fields=['extra_config'])
                    logger.info("[MattermostPassthroughHandler] Session token obtained and cached")
                    return {'sessionid': token}
            
            logger.warning("[MattermostPassthroughHandler] Login failed: %s", resp.status_code)
        except Exception as exc:
            logger.warning("[MattermostPassthroughHandler] get_upstream_cookies failed: %s", exc)
        return {}

    def rewrite_upstream_body(self, body, content_type, request, **kwargs):
        """
        Rewrite non-HTML response bodies if needed.
        Returns None to use original body, or modified bytes.
        """
        # Most API responses pass through unchanged
        return None

    def _strip_base_tags(self, html):
        """Remove <base> tags that break relative URLs in embedded context."""
        if not html:
            return html
        return re.sub(r"<base\b[^>]*>", "", html, flags=re.IGNORECASE)

    def _strip_meta_redirects(self, html):
        """Remove meta refresh tags that navigate away from embed."""
        if not html:
            return html
        return re.sub(
            r'<meta\s+http-equiv\s*=\s*["\'"]refresh["\'"][^>]*>',
            "", html, flags=re.IGNORECASE,
        )

    def _strip_csp(self, html):
        """Remove Content-Security-Policy meta tags."""
        if not html:
            return html
        return re.sub(
            r'<meta\s+http-equiv\s*=\s*["\'"]Content-Security-Policy["\'"][^>]*>',
            "", html, flags=re.IGNORECASE,
        )

    def _inject_client_shim(self, html, base_origin, request):
        """
        Inject JavaScript shim that:
        - Rewrites all URLs to go through /pt/admin/mattermost/
        - Patches fetch, XHR, WebSocket to use proxy
        - Seeds session token for SPA authentication
        """
        proxy_prefix = "/pt/admin/mattermost"
        
        shim = """
<script data-polysaas-mattermost-shim="1">
(function() {
    var B = """ + json.dumps(base_origin) + """;  // Upstream origin
    var PROXY = """ + json.dumps(proxy_prefix) + """;  // PolySaaS proxy prefix
    var O = window.location.origin;  // PolySaaS origin
    
    // PolySaaS paths - never rewrite these
    var PS_PREFIXES = ['/static/admin/', '/static/img/', '/admin/', '/dose/', '/media/', '/accounts/', '/pt/', '/favicon'];
    function isPolySaaSPath(s) {
        for (var i = 0; i < PS_PREFIXES.length; i++) {
            if (s.startsWith(PS_PREFIXES[i])) return true;
        }
        return false;
    }
    
    // Rewrite URL to go through proxy
    function toProxy(s) {
        if (typeof s !== 'string') return s;
        if (!s || s.startsWith('data:') || s.startsWith('blob:')) return s;
        
        // Absolute URL to upstream - rewrite to proxy
        if (s.startsWith(B)) {
            var tail = s.slice(B.length);
            if (!tail.startsWith('/')) tail = '/' + tail;
            return PROXY + tail;
        }
        
        // Absolute URL to PolySaaS - strip origin
        if (s.startsWith(O + '/')) s = s.slice(O.length);
        else if (s.startsWith('http:') || s.startsWith('https:') || s.indexOf('//') === 0) return s;
        
        if (s.charAt(0) !== '/') return s;
        
        // PolySaaS paths stay untouched
        if (isPolySaaSPath(s)) return s;
        
        // All other paths go through proxy
        return PROXY + s;
    }
    
    // Patch fetch
    var _f = window.fetch;
    window.fetch = function(input, init) {
        if (typeof input === 'string') {
            input = toProxy(input);
        } else if (typeof Request !== 'undefined' && input instanceof Request) {
            var u = toProxy(input.url);
            if (u !== input.url) input = new Request(u, input);
        }
        return _f.call(this, input, init);
    };
    
    // Patch XMLHttpRequest
    var _xo = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {
        var rest = Array.prototype.slice.call(arguments, 2);
        return _xo.apply(this, [method, toProxy(url)].concat(rest));
    };
    
    // Patch WebSocket
    var _WS = WebSocket;
    window.WebSocket = function(url, protocols) {
        if (typeof url === 'string') {
            try {
                var u = new URL(url, location.href);
                u.hostname = location.hostname;
                u.port = location.port || '';
                u.protocol = (location.protocol === 'https:') ? 'wss:' : 'ws:';
                if (!u.pathname.startsWith('/pt/')) {
                    u.pathname = PROXY + u.pathname;
                }
                url = u.toString();
                console.log('[PolySaaS] WebSocket through proxy:', url);
            } catch(e) { console.log('[PolySaaS] WebSocket rewrite error:', e); }
        }
        return protocols === undefined ? new _WS(url) : new _WS(url, protocols);
    };
    
    // Patch element src/href setters
    function patchProp(proto, prop) {
        var d = Object.getOwnPropertyDescriptor(proto, prop);
        if (!d || !d.set) return;
        Object.defineProperty(proto, prop, {
            get: d.get,
            set: function(v) {
                if (typeof v === 'string') v = toProxy(v);
                d.set.call(this, v);
            },
            configurable: true, enumerable: true
        });
    }
    patchProp(HTMLScriptElement.prototype, 'src');
    patchProp(HTMLLinkElement.prototype, 'href');
    patchProp(HTMLImageElement.prototype, 'src');
    
    // Patch setAttribute
    var _setAttr = Element.prototype.setAttribute;
    Element.prototype.setAttribute = function(name, value) {
        if (typeof value === 'string') {
            var ln = name.toLowerCase();
            if ((ln === 'src' || ln === 'href') &&
                (this instanceof HTMLScriptElement || this instanceof HTMLLinkElement || this instanceof HTMLImageElement)) {
                value = toProxy(value);
            }
        }
        return _setAttr.call(this, name, value);
    };
    
    console.log('[PolySaaS] mattermost shim loaded - all traffic routed through', PROXY);
})();
</script>
"""
        
        # Inject shim after <head>
        lower = html.lower()
        idx = lower.find("<head>")
        if idx != -1:
            ins = idx + len("<head>")
            return html[:ins] + shim + html[ins:]
        if "</head>" in html:
            return html.replace("</head>", shim + "</head>", 1)
        return shim + html

