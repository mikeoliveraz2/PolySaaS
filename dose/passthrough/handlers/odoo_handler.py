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
            r'((?:href|src)=["\'])(/(?:web|odoo|bus|websocket)/[^"\']*)',
            _rewrite_attr, html,
        )

        # Rewrite url(...) inside inline <style> blocks (covers @font-face and background-image)
        def _rewrite_css_url(m):
            quote = m.group(1) or ''
            path  = m.group(2)
            close = m.group(3) or ''
            if path.startswith('/web/') or path.startswith('/odoo/') or path.startswith('/bus/') or path.startswith('/websocket'):
                path = '/pt/admin/odoo' + path
            return f'url({quote}{path}{close})'

        html = re.sub(
            r'url\((["\']?)(/(?:web|odoo|bus|websocket)/[^)"\']*)(["\']?)\)',
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
        base_tag = f'<base href="{proxy_prefix}/">'
        
        patch = f"""
{base_tag}
<style id="polysaas-odoo-container-fix">
/* Prevent Odoo's bundled CSS from hijacking html/body layout */
body.polysaas-passthrough-embed-page,
html {{
    height: auto !important;
    overflow: visible !important;
}}
/* Scope container fills the content area slot */
.polysaas-passthrough-scope {{
    position: relative !important;
    width: 100%;
    height: calc(100vh - 98px);
    overflow: hidden;
    box-sizing: border-box;
}}
/* Pin #wrapwrap inside the scope — defeat Odoo's position:fixed */
.polysaas-passthrough-scope #wrapwrap,
.polysaas-passthrough-scope .o_web_client,
.polysaas-passthrough-scope .o_action_manager {{
    position: relative !important;
    top: 0 !important;
    left: 0 !important;
    right: auto !important;
    bottom: auto !important;
    width: 100% !important;
    height: 100% !important;
    min-height: unset !important;
    max-height: unset !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
}}
</style>
<script data-polysaas-odoo-shim="1">
(function() {{
var B = {base_json};       // upstream origin e.g. http://localhost:8069
var S = {session_json};    // server-side session_id (bootstrap only)
var PROXY = {proxy_json};
var O = window.location.origin;

console.log('[PolySaaS] Odoo shim starting, B=', B, 'O=', O);

// Seed session_id cookie so Odoo's SPA considers the user logged in on boot.
if (S) {{
  try {{
    document.cookie = 'session_id=' + S + '; path=/; SameSite=Lax';
  }} catch(e) {{}}
}}

// PolySaaS-owned paths — never rewrite these to upstream
var PS_PREFIXES = ['/static/admin/', '/static/img/', '/static/fonts/', '/static/css/',
                   '/static/js/', '/admin/', '/dose/', '/media/', '/accounts/', '/pt/', '/favicon'];
function isPolySaaSPath(s) {{
  for (var i = 0; i < PS_PREFIXES.length; i++) {{
    if (s.startsWith(PS_PREFIXES[i])) return true;
  }}
  return false;
}}

// Odoo API/action paths that must flow through the PolySaaS proxy
var ODOO_API_PREFIXES = ['/web/', '/odoo/', '/api/', '/longpolling/', '/bus/', '/websocket'];
function isOdooApiPath(s) {{
  for (var i = 0; i < ODOO_API_PREFIXES.length; i++) {{
    if (s.startsWith(ODOO_API_PREFIXES[i])) return true;
  }}
  return false;
}}

function toProxy(s) {{
  if (typeof s !== 'string' || !s) return s;
  if (s.startsWith('data:') || s.startsWith('blob:')) return s;
  if (s.startsWith(B)) return s;                           // already upstream-absolute
  if (s.startsWith(O + '/')) s = s.slice(O.length);       // strip our own origin
  else if (s.startsWith('http:') || s.startsWith('https:') || s.indexOf('//') === 0) return s;
  if (s.charAt(0) !== '/') return s;
  if (isPolySaaSPath(s)) return s;                         // PolySaaS asset — untouched
  if (isOdooApiPath(s)) return PROXY + s;                  // Odoo API → through proxy
  return B + s;                                            // everything else → direct upstream
}}

// Patch fetch
var _f = window.fetch;
window.fetch = function(input, init) {{
  var url = (typeof input === 'string') ? input : (input instanceof Request ? input.url : '');
  var proxied = toProxy(url);
  if (url !== proxied) console.log('[PolySaaS] fetch proxied:', url, '->', proxied);
  
  if (typeof input === 'string') input = proxied;
  else if (typeof Request !== 'undefined' && input instanceof Request) {{
    if (proxied !== input.url) input = new Request(proxied, input);
  }}
  return _f.call(this, input, init);
}};

// Patch XHR
var _xo = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(method, url) {{
  var proxied = toProxy(url);
  if (url !== proxied) console.log('[PolySaaS] XHR proxied:', url, '->', proxied);
  var rest = Array.prototype.slice.call(arguments, 2);
  return _xo.apply(this, [method, proxied].concat(rest));
}};

// ── URL GUARD (Active Redirect) ──
function fixUrl(url) {{
  if (!url || typeof url !== 'string') return url;
  if (url.startsWith('/') && !url.startsWith(PROXY) && !isPolySaaSPath(url)) {{
    if (url.startsWith('/web') || url.startsWith('/odoo') || url.startsWith('/bus') || url.startsWith('/websocket')) {{
       console.log('[PolySaaS] URL Guard: Redirecting', url, '->', PROXY + url);
       return PROXY + url;
    }}
  }}
  return url;
}}

var _locReplace = Location.prototype.replace;
Location.prototype.replace = function(url) {{
  var fixed = fixUrl(url);
  if (fixed !== url) {{ window.location.href = fixed; return; }}
  return _locReplace.call(this, url);
}};
var _locAssign = Location.prototype.assign;
Location.prototype.assign = function(url) {{
  var fixed = fixUrl(url);
  if (fixed !== url) {{ window.location.href = fixed; return; }}
  return _locAssign.call(this, url);
}};
try {{
  var hrefDesc = Object.getOwnPropertyDescriptor(Location.prototype, 'href');
  if (hrefDesc && hrefDesc.set) {{
    Object.defineProperty(Location.prototype, 'href', {{
      get: function() {{ return hrefDesc.get.call(this); }},
      set: function(v) {{
        var fixed = fixUrl(v);
        if (fixed !== v) {{ window.location.href = fixed; return; }}
        hrefDesc.set.call(this, v);
      }},
      configurable: true, enumerable: true,
    }});
  }}
}} catch(e) {{}}

// Tell Odoo router we are at "/" so it recognises the route
try {{ history.replaceState(null, '', '/'); }} catch(e) {{}}

// ── ADAPTIVE UI SHIM ──
var scopeSelector = '.polysaas-passthrough-scope';
function getWidth() {{
  var scope = document.querySelector(scopeSelector);
  if (scope) return scope.offsetWidth;
  var content = document.querySelector('.content-wrapper') || document.querySelector('.content');
  return content ? content.offsetWidth : window.innerWidth;
}}
function getHeight() {{
  var scope = document.querySelector(scopeSelector);
  if (scope) return scope.offsetHeight;
  return window.innerHeight;
}}
try {{
  Object.defineProperty(window, 'innerWidth', {{ get: function() {{ return getWidth(); }}, configurable: true }});
  Object.defineProperty(window, 'innerHeight', {{ get: function() {{ return getHeight(); }}, configurable: true }});
  var _matchMedia = window.matchMedia;
  window.matchMedia = function(query) {{
    if (query.indexOf('width') !== -1 || query.indexOf('height') !== -1) {{
      var width = getWidth(), height = getHeight();
      var wMatch = query.match(/(min|max)-width:\s*(\d+)px/);
      if (wMatch) {{
        var res = (wMatch[1] === 'min') ? (width >= parseInt(wMatch[2])) : (width <= parseInt(wMatch[2]));
        return {{ matches: res, media: query, onchange: null, addListener: function(){{}}, removeListener: function(){{}}, addEventListener: function(){{}}, removeEventListener: function(){{}}, dispatchEvent: function(){{ return false; }} }};
      }}
    }}
    return _matchMedia.call(window, query);
  }};
}} catch(e) {{}}

// ── WORKER & BUS SHIM ──
var _W = window.Worker;
window.Worker = function(url, options) {{
  var proxied = toProxy(url);
  console.log('[PolySaaS] Worker starting:', url, '->', proxied);
  return new _W(proxied, options);
}};
try {{
  if (window.odoo && window.odoo.info) {{
    window.odoo.info.websocket = false; 
    console.log('[PolySaaS] Forced Odoo to fallback to long-polling');
  }}
}} catch(e) {{}}

}})();
</script>
"""
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

                if patched != text:
                    logger.info(
                        "[ODOO HANDLER] Patched Owl mount(document.body) and paths in JS"
                    )
                    return patched.encode('utf-8', errors='ignore')
            except Exception as exc:
                logger.warning("[ODOO HANDLER] JS mount patch failed: %s", exc)
            return None

        return None
