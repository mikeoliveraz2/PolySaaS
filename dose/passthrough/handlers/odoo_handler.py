# dose/passthrough/handlers/odoo_handler.py
"""
Odoo SPA passthrough handler.

Lessons applied directly from the Mattermost 26-hour debug session:
  BUG1  HTTP_COOKIE never forwarded as header — use cookies= param only
  BUG2  HTTP_ prefix stripped from all outbound headers (fixed in forwarding.py)
  BUG3  Browser session_id takes priority over server-cached token
  BUG4  Set-Cookie forwarded by forwarding.py automatically
  BUG7  CSP stripped (both meta tag and response header)
  BUG8  <base> tag stripped
  BUG9  API calls route through proxy; statics direct to upstream
  BUG10 Navigation lock on hard-nav only, not history.*
"""

import json
import logging
import re
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class OdooPassthroughHandler:

    # ------------------------------------------------------------------ #
    # Server-side auto-login                                               #
    # ------------------------------------------------------------------ #

    def get_upstream_cookies(self, request):
        """
        Return a valid Odoo session_id cookie.
        Uses JSON-RPC /web/session/authenticate.
        Cached in TenantApp.extra_config with a 1-hour TTL.
        """
        try:
            from dose.models import TenantApp
            from dose.utils import get_current_tenant
            import requests as _req

            tenant = get_current_tenant(request)
            if not tenant:
                return {}
            ta = TenantApp.objects.filter(
                tenant=tenant, app_name='odoo', status='active',
            ).first()
            if not ta or not ta.extra_config:
                return {}

            # Return cached session if still fresh (< 1 hour)
            session_id = ta.extra_config.get('odoo_session_id')
            session_time = ta.extra_config.get('odoo_session_time', 0)
            if session_id and (time.time() - session_time < 3600):
                return {'session_id': session_id}
            if session_id:
                logger.info("[ODOO HANDLER] Session TTL expired — refreshing")

            password = ta.extra_config.get('odoo_password')
            if not password:
                logger.warning("[ODOO HANDLER] No odoo_password in extra_config")
                return {}

            login_id = ta.extra_config.get('odoo_login') or (request.user.username or '').lower()
            db_name  = ta.extra_config.get('odoo_db') or 'odoo'

            # Resolve Odoo base URL from the PassThroughEndpoint
            odoo_url = 'http://localhost:8069'
            try:
                from dose.models import PassThroughEndpoint
                ep = PassThroughEndpoint.objects.filter(
                    trigger_path__iexact='odoo', is_enabled=True
                ).first()
                if ep:
                    p = urlparse(ep.endpoint_url)
                    odoo_url = f"{p.scheme}://{p.netloc}"
            except Exception:
                pass

            resp = _req.post(
                f'{odoo_url}/web/session/authenticate',
                json={
                    'jsonrpc': '2.0',
                    'method': 'call',
                    'id': 1,
                    'params': {
                        'db': db_name,
                        'login': login_id,
                        'password': password,
                    },
                },
                timeout=10,
            )
            if resp.status_code == 200:
                body = resp.json()
                uid = (body.get('result') or {}).get('uid')
                sid = resp.cookies.get('session_id')
                if uid and sid:
                    ta.extra_config['odoo_session_id']   = sid
                    ta.extra_config['odoo_session_time'] = time.time()
                    ta.save(update_fields=['extra_config'])
                    logger.info("[ODOO HANDLER] Session obtained for %s (uid=%s)", login_id, uid)
                    return {'session_id': sid}
                else:
                    logger.warning("[ODOO HANDLER] Login returned uid=%s sid=%s — bad credentials?", uid, sid)
            else:
                logger.warning("[ODOO HANDLER] /web/session/authenticate -> %s", resp.status_code)
        except Exception as exc:
            logger.warning("[ODOO HANDLER] get_upstream_cookies failed: %s", exc)
        return {}

    # ------------------------------------------------------------------ #
    # HTML processing                                                      #
    # ------------------------------------------------------------------ #

    def process_html_response(self, html_str, request, endpoint_url=None, *args, **kwargs):
        logger.info("[ODOO HANDLER] Processing HTML")

        if not endpoint_url:
            return html_str, None

        parsed      = urlparse(endpoint_url.rstrip('/'))
        base_origin = f"{parsed.scheme}://{parsed.netloc}"

        session_id = (self.get_upstream_cookies(request) or {}).get('session_id') or ''

        html_str = self._strip_base_tags(html_str)
        html_str = self._strip_meta_redirects(html_str)
        html_str = self._strip_csp(html_str)
        # Rewrite initial HTML asset paths BEFORE the JS shim runs.
        # <link> and <script> tags are fetched by the browser before JS executes, so we must
        # rewrite them server-side to route through our proxy.
        html_str = self._rewrite_static_paths(html_str)
        html_str = self._inject_client_shim(html_str, base_origin, session_id=session_id)

        return html_str, None

    def _rewrite_static_paths(self, html):
        """
        Rewrite src/href attributes in <link>/<script>/<img> tags that start with /web/, /odoo/,
        or /bus/ to go through our PolySaaS proxy at /pt/admin/odoo/.
        This must happen server-side because the browser fetches these before JS runs.
        Also rewrites CSS url() references inside <style> blocks (for @font-face).
        """
        def _rewrite_attr(m):
            prefix = m.group(1)
            path   = m.group(2)
            if path.startswith('/web/') or path.startswith('/odoo/') or path.startswith('/bus/') or path.startswith('/websocket'):
                path = '/pt/admin/odoo' + path
            return prefix + path

        # Rewrite href="..." and src="..." in tag attributes
        html = re.sub(
            r'((?:href|src)=["\'])(/(?:web|odoo|bus|websocket)[^"\']*)',
            _rewrite_attr, html,
        )

        # Rewrite url(...) inside inline <style> blocks (covers @font-face and background-image)
        def _rewrite_css_url(m):
            quote = m.group(1) or ''
            path  = m.group(2)
            close = m.group(3) or ''
            if path.startswith('/web') or path.startswith('/odoo') or path.startswith('/bus') or path.startswith('/websocket'):
                path = '/pt/admin/odoo' + path
            return f'url({quote}{path}{close})'

        html = re.sub(
            r'url\((["\']?)(/(?:web|odoo|bus|websocket)[^)"\']*)(["\']?)\)',
            _rewrite_css_url, html,
        )
        return html

    # ------------------------------------------------------------------ #
    # HTML cleaners                                                        #
    # ------------------------------------------------------------------ #

    def _strip_base_tags(self, html):
        """Odoo ships <base href="/odoo/"> which breaks the Jazzmin embed."""
        return re.sub(r'<base\b[^>]*>', '', html, flags=re.IGNORECASE)

    def _strip_meta_redirects(self, html):
        return re.sub(
            r'<meta\s+http-equiv\s*=\s*["\']refresh["\'][^>]*>',
            '', html, flags=re.IGNORECASE,
        )

    def _strip_csp(self, html):
        return re.sub(
            r'<meta\s+http-equiv\s*=\s*["\']Content-Security-Policy["\'][^>]*>',
            '', html, flags=re.IGNORECASE,
        )

    # ------------------------------------------------------------------ #
    # Client-side shim                                                     #
    # ------------------------------------------------------------------ #

    def _inject_client_shim(self, html, base_origin, session_id=''):
        base_json    = json.dumps(base_origin)
        session_json = json.dumps(session_id)
        proxy_prefix = '/pt/admin/odoo'
        proxy_json   = json.dumps(proxy_prefix)

        # ── Odoo 18 Base Path Fix ──
        # Odoo 18 often uses a <base> tag or internal logic that assumes it is at /odoo/
        # We must ensure the browser knows the base for relative assets is the proxy path.
        base_tag = '<base href="' + proxy_prefix + '/">'
        
        # Use a standard string with .replace() to avoid f-string { } conflicts entirely.
        # COMPREHENSIVE FIX for Fix #4: No apps / no adaptive display
        patch_template = """
BASE_TAG
<style id="polysaas-odoo-comprehensive-fix">
/* ═══════════════════════════════════════════════════════════════════════════
   POLYSAAS ODOO COMPREHENSIVE FIX
   Problem: Odoo shows blank screen unless full-screen toggle is used
   Root cause: Odoo's Owl framework uses position:fixed and 100vh which breaks
   when embedded in a constrained container.
   ═══════════════════════════════════════════════════════════════════════════ */

/* 1. Reset html/body to allow content flow */
html, body {
    height: auto !important;
    min-height: 100% !important;
    overflow: visible !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* 2. The scope container is the new viewport for Odoo */
.polysaas-passthrough-scope {
    position: relative !important;
    width: 100% !important;
    height: calc(100vh - 98px) !important;
    min-height: 400px !important;
    overflow: hidden !important;
    box-sizing: border-box !important;
    background: #f8f9fa !important;
}

/* 3. Force Odoo's root elements to fill the scope, not the viewport */
.polysaas-passthrough-scope #wrapwrap,
.polysaas-passthrough-scope .o_web_client {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    width: 100% !important;
    height: 100% !important;
    min-height: 100% !important;
    max-height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* 4. Odoo navbar stays at top */
.polysaas-passthrough-scope .o_navbar {
    position: relative !important;
    flex: 0 0 46px !important;
    height: 46px !important;
    min-height: 46px !important;
    max-height: 46px !important;
    width: 100% !important;
    z-index: 100 !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* 5. Action manager fills remaining space */
.polysaas-passthrough-scope .o_action_manager {
    position: relative !important;
    flex: 1 1 auto !important;
    height: calc(100% - 46px) !important;
    min-height: 0 !important;
    overflow: auto !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* 6. Apps board (the grid of app icons) */
.polysaas-passthrough-scope .o_apps,
.polysaas-passthrough-scope .o_home_menu,
.polysaas-passthrough-scope .o_app_board {
    display: flex !important;
    flex-wrap: wrap !important;
    justify-content: flex-start !important;
    align-content: flex-start !important;
    padding: 20px !important;
    gap: 20px !important;
    visibility: visible !important;
    opacity: 1 !important;
    min-height: 200px !important;
}

/* 7. Individual app icons */
.polysaas-passthrough-scope .o_app,
.polysaas-passthrough-scope .o_menuitem {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100px !important;
    height: 100px !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* 8. Content areas */
.polysaas-passthrough-scope .o_content,
.polysaas-passthrough-scope .o_view_controller,
.polysaas-passthrough-scope .o_kanban_view,
.polysaas-passthrough-scope .o_list_view,
.polysaas-passthrough-scope .o_form_view {
    position: relative !important;
    width: 100% !important;
    height: 100% !important;
    overflow: auto !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* 9. Override any fixed positioning that escapes the container */
.polysaas-passthrough-scope [style*="position: fixed"],
.polysaas-passthrough-scope [style*="position:fixed"] {
    position: absolute !important;
}

/* 10. Ensure loading spinners and overlays stay in scope */
.polysaas-passthrough-scope .o_loading,
.polysaas-passthrough-scope .o_blockUI {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
}

/* 11. Debug: make sure we can see if content is there */
.polysaas-passthrough-scope:empty::after {
    content: "Loading Odoo..." !important;
    display: block !important;
    padding: 40px !important;
    text-align: center !important;
    color: #666 !important;
}
</style>
<script data-polysaas-odoo-shim="1">
(function() {
'use strict';

var B = BASE_JSON;       // upstream origin e.g. http://localhost:8069
var S = SESSION_JSON;    // server-side session_id (bootstrap only)
var PROXY = PROXY_JSON;
var O = window.location.origin;
var SCOPE_SELECTOR = '.polysaas-passthrough-scope';

console.log('[PolySaaS Odoo] Shim starting, upstream=' + B + ', origin=' + O);

// ═══════════════════════════════════════════════════════════════════════════
// 1. SESSION COOKIE SEEDING
// ═══════════════════════════════════════════════════════════════════════════
if (S) {
    try {
        document.cookie = 'session_id=' + S + '; path=/; SameSite=Lax';
        console.log('[PolySaaS Odoo] Session cookie seeded');
    } catch(e) {
        console.warn('[PolySaaS Odoo] Failed to seed session cookie:', e);
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// 2. PATH CLASSIFICATION
// ═══════════════════════════════════════════════════════════════════════════
var PS_PREFIXES = ['/static/admin/', '/static/img/', '/static/fonts/', '/static/css/',
                   '/static/js/', '/admin/', '/dose/', '/media/', '/accounts/', '/pt/', '/favicon'];

function isPolySaaSPath(s) {
    if (!s || typeof s !== 'string') return false;
    for (var i = 0; i < PS_PREFIXES.length; i++) {
        if (s.indexOf(PS_PREFIXES[i]) === 0) return true;
    }
    return false;
}

var ODOO_API_PREFIXES = ['/web/', '/odoo/', '/api/', '/longpolling/', '/bus/', '/websocket'];

function isOdooApiPath(s) {
    if (!s || typeof s !== 'string') return false;
    for (var i = 0; i < ODOO_API_PREFIXES.length; i++) {
        if (s.indexOf(ODOO_API_PREFIXES[i]) === 0) return true;
    }
    return false;
}

// ═══════════════════════════════════════════════════════════════════════════
// 3. URL REWRITING
// CRITICAL: ALL Odoo traffic MUST flow through /pt/admin/odoo/
// This enables: PolySniffer capture, dynamic orchestration, Instruction triggers, Atomic Services
// The /pt/ prefix tells ExternalPassthroughMiddleware to handle it.
// DO NOT route anything direct to upstream (B) - that bypasses the entire PolySaaS value.
// See Process Rule 1: No Unilateral Changes
// ═══════════════════════════════════════════════════════════════════════════
function toProxy(s) {
    if (typeof s !== 'string' || !s) return s;
    if (s.indexOf('data:') === 0 || s.indexOf('blob:') === 0) return s;
    // Absolute URL to upstream — rewrite to go through proxy
    if (s.indexOf(B) === 0) {
        var tail = s.slice(B.length);
        if (tail.charAt(0) !== '/') tail = '/' + tail;
        return PROXY + tail;
    }
    if (s.indexOf(O + '/') === 0) s = s.slice(O.length);  // strip our origin
    if (s.indexOf('http:') === 0 || s.indexOf('https:') === 0 || s.indexOf('//') === 0) return s;
    if (s.charAt(0) !== '/') return s;
    // PolySaaS paths stay untouched
    if (isPolySaaSPath(s)) return s;
    // ALL Odoo paths go through proxy - no exceptions
    return PROXY + s;
}

// ═══════════════════════════════════════════════════════════════════════════
// 4. FETCH PATCHING
// ═══════════════════════════════════════════════════════════════════════════
var _fetch = window.fetch;
window.fetch = function(input, init) {
    var url = (typeof input === 'string') ? input : (input && input.url ? input.url : '');
    var proxied = toProxy(url);
    if (url !== proxied) {
        console.log('[PolySaaS Odoo] fetch:', url, '->', proxied);
    }
    if (typeof input === 'string') {
        input = proxied;
    } else if (input && input.url && proxied !== input.url) {
        input = new Request(proxied, input);
    }
    return _fetch.call(this, input, init);
};

// ═══════════════════════════════════════════════════════════════════════════
// 5. XHR PATCHING
// ═══════════════════════════════════════════════════════════════════════════
var _xhrOpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(method, url) {
    var proxied = toProxy(url);
    if (url !== proxied) {
        console.log('[PolySaaS Odoo] XHR:', url, '->', proxied);
    }
    var args = Array.prototype.slice.call(arguments);
    args[1] = proxied;
    return _xhrOpen.apply(this, args);
};

// ═══════════════════════════════════════════════════════════════════════════
// 6. WEBSOCKET PATCHING - Critical for Odoo 18 bus
// ═══════════════════════════════════════════════════════════════════════════
var _WebSocket = window.WebSocket;
window.WebSocket = function(url, protocols) {
    var proxied = toProxy(url);
    // Convert relative URL to absolute WebSocket URL
    if (proxied.charAt(0) === '/') {
        var wsProto = (window.location.protocol === 'https:') ? 'wss://' : 'ws://';
        proxied = wsProto + window.location.host + proxied;
    }
    console.log('[PolySaaS Odoo] WebSocket:', url, '->', proxied);
    if (protocols !== undefined) {
        return new _WebSocket(proxied, protocols);
    }
    return new _WebSocket(proxied);
};
// Copy static properties
if (_WebSocket.CONNECTING !== undefined) window.WebSocket.CONNECTING = _WebSocket.CONNECTING;
if (_WebSocket.OPEN !== undefined) window.WebSocket.OPEN = _WebSocket.OPEN;
if (_WebSocket.CLOSING !== undefined) window.WebSocket.CLOSING = _WebSocket.CLOSING;
if (_WebSocket.CLOSED !== undefined) window.WebSocket.CLOSED = _WebSocket.CLOSED;

// ═══════════════════════════════════════════════════════════════════════════
// 7. URL GUARD - Prevent navigation to un-proxied paths
// ═══════════════════════════════════════════════════════════════════════════
function guardUrl(url) {
    if (!url || typeof url !== 'string') return url;
    // If it's a bare Odoo path without proxy prefix, add it
    if (url.charAt(0) === '/' && !isPolySaaSPath(url) && url.indexOf(PROXY) !== 0) {
        if (url.indexOf('/web') === 0 || url.indexOf('/odoo') === 0 || 
            url.indexOf('/bus') === 0 || url.indexOf('/websocket') === 0) {
            console.log('[PolySaaS Odoo] URL Guard:', url, '->', PROXY + url);
            return PROXY + url;
        }
    }
    return url;
}

// Patch history.pushState
var _pushState = history.pushState;
history.pushState = function(state, title, url) {
    var guarded = guardUrl(url);
    return _pushState.call(this, state, title, guarded);
};

// Patch history.replaceState
var _replaceState = history.replaceState;
history.replaceState = function(state, title, url) {
    var guarded = guardUrl(url);
    return _replaceState.call(this, state, title, guarded);
};

// Patch Location methods
var _locReplace = Location.prototype.replace;
Location.prototype.replace = function(url) {
    var guarded = guardUrl(url);
    return _locReplace.call(this, guarded);
};

var _locAssign = Location.prototype.assign;
Location.prototype.assign = function(url) {
    var guarded = guardUrl(url);
    return _locAssign.call(this, guarded);
};

// Patch location.href setter
try {
    var hrefDesc = Object.getOwnPropertyDescriptor(Location.prototype, 'href');
    if (hrefDesc && hrefDesc.set) {
        Object.defineProperty(Location.prototype, 'href', {
            get: hrefDesc.get,
            set: function(v) {
                var guarded = guardUrl(v);
                return hrefDesc.set.call(this, guarded);
            },
            configurable: true,
            enumerable: true
        });
    }
} catch(e) {
    console.warn('[PolySaaS Odoo] Could not patch location.href:', e);
}

// ═══════════════════════════════════════════════════════════════════════════
// 8. ADAPTIVE UI - Make Odoo think it has the scope's dimensions
// ═══════════════════════════════════════════════════════════════════════════
function getScopeWidth() {
    var scope = document.querySelector(SCOPE_SELECTOR);
    if (scope && scope.offsetWidth > 0) return scope.offsetWidth;
    var content = document.querySelector('.content-wrapper') || document.querySelector('.content');
    if (content && content.offsetWidth > 0) return content.offsetWidth;
    return 1200; // fallback
}

function getScopeHeight() {
    var scope = document.querySelector(SCOPE_SELECTOR);
    if (scope && scope.offsetHeight > 0) return scope.offsetHeight;
    return 800; // fallback
}

// Store original values
var _innerWidth = window.innerWidth;
var _innerHeight = window.innerHeight;

try {
    Object.defineProperty(window, 'innerWidth', {
        get: function() { return getScopeWidth(); },
        configurable: true
    });
    Object.defineProperty(window, 'innerHeight', {
        get: function() { return getScopeHeight(); },
        configurable: true
    });
    console.log('[PolySaaS Odoo] innerWidth/Height patched');
} catch(e) {
    console.warn('[PolySaaS Odoo] Could not patch innerWidth/Height:', e);
}

// Patch matchMedia for responsive queries
var _matchMedia = window.matchMedia;
window.matchMedia = function(query) {
    if (query && (query.indexOf('width') !== -1 || query.indexOf('height') !== -1)) {
        var width = getScopeWidth();
        var height = getScopeHeight();
        
        // Parse min-width / max-width queries
        var minW = query.match(/min-width:\s*(\d+)px/);
        var maxW = query.match(/max-width:\s*(\d+)px/);
        var minH = query.match(/min-height:\s*(\d+)px/);
        var maxH = query.match(/max-height:\s*(\d+)px/);
        
        var matches = true;
        if (minW) matches = matches && (width >= parseInt(minW[1]));
        if (maxW) matches = matches && (width <= parseInt(maxW[1]));
        if (minH) matches = matches && (height >= parseInt(minH[1]));
        if (maxH) matches = matches && (height <= parseInt(maxH[1]));
        
        return {
            matches: matches,
            media: query,
            onchange: null,
            addListener: function() {},
            removeListener: function() {},
            addEventListener: function() {},
            removeEventListener: function() {},
            dispatchEvent: function() { return false; }
        };
    }
    return _matchMedia.call(window, query);
};

// ═══════════════════════════════════════════════════════════════════════════
// 9. WORKER PATCHING
// ═══════════════════════════════════════════════════════════════════════════
var _Worker = window.Worker;
window.Worker = function(url, options) {
    var proxied = toProxy(url);
    console.log('[PolySaaS Odoo] Worker:', url, '->', proxied);
    return new _Worker(proxied, options);
};

// ═══════════════════════════════════════════════════════════════════════════
// 10. FORCE LONG-POLLING FALLBACK (WebSocket may not work through proxy)
// ═══════════════════════════════════════════════════════════════════════════
function disableWebSocket() {
    try {
        if (window.odoo && window.odoo.info) {
            window.odoo.info.websocket = false;
            console.log('[PolySaaS Odoo] Forced long-polling fallback');
        }
    } catch(e) {}
}
// Try immediately and also after a delay (Odoo may not be initialized yet)
disableWebSocket();
setTimeout(disableWebSocket, 100);
setTimeout(disableWebSocket, 500);
setTimeout(disableWebSocket, 1000);

// ═══════════════════════════════════════════════════════════════════════════
// 11. OWL MOUNT INTERCEPTION - Redirect mount target to scope
// ═══════════════════════════════════════════════════════════════════════════
// Odoo's Owl framework mounts to document.body by default.
// We need to intercept this and redirect to our scope container.
var _appendChild = Element.prototype.appendChild;
Element.prototype.appendChild = function(child) {
    // If Odoo is trying to append to document.body and it looks like the web client
    if (this === document.body && child && child.classList) {
        if (child.classList.contains('o_web_client') || 
            child.id === 'wrapwrap' ||
            child.classList.contains('o_home_menu')) {
            var scope = document.querySelector(SCOPE_SELECTOR);
            if (scope) {
                console.log('[PolySaaS Odoo] Redirecting appendChild to scope:', child.className || child.id);
                return _appendChild.call(scope, child);
            }
        }
    }
    return _appendChild.call(this, child);
};

// ═══════════════════════════════════════════════════════════════════════════
// 12. MUTATION OBSERVER - Catch any elements that escape to body
// ═══════════════════════════════════════════════════════════════════════════
function moveOdooElementsToScope() {
    var scope = document.querySelector(SCOPE_SELECTOR);
    if (!scope) return;
    
    // Elements that should be inside the scope
    var selectors = ['#wrapwrap', '.o_web_client', '.o_home_menu', '.o_apps'];
    
    selectors.forEach(function(sel) {
        var el = document.body.querySelector(':scope > ' + sel);
        if (el && el.parentElement === document.body) {
            console.log('[PolySaaS Odoo] Moving escaped element to scope:', sel);
            scope.appendChild(el);
        }
    });
}

// Run periodically to catch late-mounting elements
setTimeout(moveOdooElementsToScope, 100);
setTimeout(moveOdooElementsToScope, 500);
setTimeout(moveOdooElementsToScope, 1000);
setTimeout(moveOdooElementsToScope, 2000);

// Also use MutationObserver for real-time catching
var observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1 && node.parentElement === document.body) {
                    if (node.classList && (
                        node.classList.contains('o_web_client') ||
                        node.classList.contains('o_home_menu') ||
                        node.id === 'wrapwrap'
                    )) {
                        var scope = document.querySelector(SCOPE_SELECTOR);
                        if (scope) {
                            console.log('[PolySaaS Odoo] MutationObserver caught:', node.className || node.id);
                            scope.appendChild(node);
                        }
                    }
                }
            });
        }
    });
});

// Start observing once DOM is ready
if (document.body) {
    observer.observe(document.body, { childList: true });
} else {
    document.addEventListener('DOMContentLoaded', function() {
        observer.observe(document.body, { childList: true });
    });
}

console.log('[PolySaaS Odoo] Shim initialization complete');

})();
</script>
"""
        patch = patch_template.replace('BASE_TAG', base_tag)
        patch = patch.replace('BASE_JSON', base_json)
        patch = patch.replace('SESSION_JSON', session_json)
        patch = patch.replace('PROXY_JSON', proxy_json)
        
        return html.replace('<head>', '<head>' + patch)

    def rewrite_upstream_body(self, body, ct, request, endpoint_url=None, upstream_path=None):
        """
        Server-side body rewriting for Odoo.
        Intercepts JavaScript bundles to redirect Owl's mount target.
        """
        if 'javascript' in ct:
            try:
                text = body.decode('utf-8', errors='ignore')
                # Owl's App.mount() and the standalone mount() helper both use
                # document.body as the container target.  Replace it with the
                # PolySaaS scope div so Odoo renders inside the embed column.
                SCOPE = '.polysaas-passthrough-scope'
                REPLACEMENT = (
                    f'.mount(document.querySelector("{SCOPE}")||document.body'
                )
                patched = text.replace(
                    '.mount(document.body', REPLACEMENT
                )

                # Also rewrite paths hidden in JS strings
                def _proxy_css_url(m):
                    quote = m.group(1) or ''
                    path  = m.group(2)
                    close = m.group(3) or ''
                    if path.startswith('/web/') or path.startswith('/odoo/') or path.startswith('/bus/') or path.startswith('/websocket'):
                        path = '/pt/admin/odoo' + path
                    return f'url({quote}{path}{close})'

                patched = re.sub(
                    r'url\((["\']?)(/(?:web|odoo|bus|websocket)/[^)"\']*)(["\']?)\)',
                    _proxy_css_url, patched,
                )

                # === FIX WEBSOCKET 404 - Force Odoo to use proxied WebSocket path ===
                if '/websocket' in patched or 'websocket' in patched.lower():
                    # Replace any direct WebSocket URLs with the proxied version
                    # Note: Using the /pt/admin/odoo prefix which is the actual proxy entry point
                    patched = patched.replace('/websocket', '/pt/admin/odoo/websocket')

                if patched != text:
                    logger.info(
                        "[ODOO HANDLER] Patched Owl mount(document.body) and paths in JS"
                    )
                    return patched.encode('utf-8', errors='ignore')
            except Exception as exc:
                logger.warning("[ODOO HANDLER] JS mount patch failed: %s", exc)
            return None

        return None
