# dose/passthrough/handlers/slack_handler.py
"""
Slack passthrough handler.

FIX 2026-08-21 (owner-approved): Slack's client builds silent-auth-refresh as a
root-relative path ("/auth?..."). Served from our origin that must be rewritten
back through our proxy prefix so the forwarder's cookie relay + CSP strip apply
(firewall / black-box model -- Slack only ever talks to our server).

FIX 2026-08-21b (owner-approved): two concrete bugs made the /auth loop spin
forever even after proxy-relay rewrite:

1. Query-param collision: PolySniffer was putting the tenant schema on the
   launch URL as ?schema=olient. Slack's own client also reads a query param
   named "schema" (numeric login-schema id). It parsed "olient" as NaN and
   logged "lc cookie (NaN) is missing" forever. Launch URLs now use
   ?_ps_tenant= instead; this handler strips _ps_tenant (and any non-numeric
   schema= poison) before the request goes upstream.

2. Wrong upstream URL: endpoint_url is a deep client path
   (https://app.slack.com/client/T.../D...), so the default forwarder join
   turned /auth into .../client/T.../D.../auth (still 200 SPA HTML, never real
   auth). Same pattern Nextcloud already uses: "/" keeps the configured deep
   link; every other path is origin + path (https://app.slack.com/auth).

FIX 2026-08-21c (owner-approved): after /auth succeeded ("credentials are
ready"), Slack's auth iframe called parent.postMessage(..., 'https://app.slack.com')
which the browser blocked because the parent origin is our proxy
(http://localhost:8000). parent.postMessage looks up the method on the PARENT
window — patching Window.prototype in the child alone never fired (confirmed:
no shim log). Now patch window + same-origin parent/top postMessage directly,
plus prototype, and rewrite message-listener event.origin so the credential
handshake completes across the proxy boundary.

BINGO: Slack Native Proxy-Relay + Host-Root Paths — 2026-08-21
"""
import re
from urllib.parse import urlparse

from dose.passthrough.handlers.handler_base import PassthroughHandlerBase

# Absolute paths Slack's client issues that must stay on the host root
# (app.slack.com/auth), never stacked under /client/... . Piccolo Passo:
# start with the confirmed /auth failure; extend only after live proof.
_SLACK_HOST_ROOT_PREFIXES = (
    "/auth",
)

_SLACK_PROXY_PATHS = _SLACK_HOST_ROOT_PREFIXES


class SlackPassthroughHandler(PassthroughHandlerBase):
    """Slack passthrough — all Slack-specific rewrite logic lives here only."""

    @classmethod
    def matches_endpoint(cls, endpoint) -> bool:
        slug = (getattr(endpoint, "slug", "") or "").lower().strip()
        if slug == "slack":
            return True
        url = (getattr(endpoint, "endpoint_url", "") or "").lower()
        return "slack.com" in url

    def needs_readable_response_body(self, request, target_url: str) -> bool:
        return True

    def upstream_url_for_subpath(self, endpoint_url, clean_path):
        """Map proxied subpaths to real Slack URLs.

        "/" keeps the configured deep client link. Every other path is
        origin + path so /auth reaches https://app.slack.com/auth, not
        .../client/T.../D.../auth. Same pattern as NextcloudPassthroughHandler.
        """
        if not endpoint_url:
            return None
        parsed = urlparse(endpoint_url)
        if not parsed.scheme or not parsed.netloc:
            return None
        origin = f"{parsed.scheme}://{parsed.netloc}"
        raw = clean_path if isinstance(clean_path, str) else "/"
        if not raw.startswith("/"):
            raw = "/" + raw
        path_only = raw.split("?", 1)[0] or "/"
        query = raw.split("?", 1)[1] if "?" in raw else ""
        if path_only in ("/", ""):
            return endpoint_url
        url = origin.rstrip("/") + path_only
        if query:
            url += "?" + query
        return url

    def filter_query_params_for_upstream(self, request, query_params: dict) -> dict:
        """Strip PolySaaS-internal params; drop non-numeric schema= poison."""
        if not query_params:
            return query_params
        filtered = {}
        for key, value in query_params.items():
            k = str(key)
            if k == "_ps_tenant":
                continue
            # Slack's schema is numeric; our tenant name is not — drop poison.
            if k == "schema" and not str(value).isdigit():
                continue
            filtered[k] = value
        return filtered

    def process_html_response(self, html_str, request, endpoint_url=None, **context):
        if not html_str:
            return html_str

        proxy_prefix = (getattr(request, "_polysniffer_proxy_prefix", None) or "").strip().rstrip("/")
        if not proxy_prefix:
            return html_str

        tenant = (
            getattr(request, "schema_name", None)
            or (getattr(getattr(request, "tenant", None), "schema_name", None) or "")
        )
        upstream_origin = ""
        if endpoint_url:
            parsed = urlparse(endpoint_url)
            if parsed.scheme and parsed.netloc:
                upstream_origin = f"{parsed.scheme}://{parsed.netloc}"
        shim = self._client_shim(proxy_prefix, tenant, upstream_origin)
        if re.search(r"(?i)<head[^>]*>", html_str):
            return re.sub(r"(?i)(<head[^>]*>)", r"\1" + shim, html_str, count=1)
        return shim + html_str

    def _client_shim(self, proxy_prefix: str, tenant_schema: str = "", upstream_origin: str = "") -> str:
        paths_js = ", ".join(f"'{p}'" for p in _SLACK_PROXY_PATHS)
        return f"""
<script data-polysaas-slack-shim="1">
(function() {{
    var PROXY_PREFIX = {proxy_prefix!r};
    var PS_TENANT = {tenant_schema!r};
    var UPSTREAM_ORIGIN = {upstream_origin!r} || 'https://app.slack.com';
    var SLACK_PATHS = [{paths_js}];

    /* Hide _ps_tenant from location.search so Slack's client does not copy it
       into /auth?... (it already has PS_TENANT in this closure for rewrites). */
    try {{
        if (window.location.search.indexOf('_ps_tenant=') !== -1) {{
            var clean = new URL(window.location.href);
            clean.searchParams.delete('_ps_tenant');
            window.history.replaceState(null, '', clean.pathname + clean.search + clean.hash);
        }}
    }} catch (e) {{}}

    /* Auth iframe does parent.postMessage(..., 'https://app.slack.com'). That
       looks up postMessage on the PARENT window object — a Window.prototype
       patch in this frame alone is not enough (confirmed live: credentials
       ready, then native targetOrigin mismatch, no shim log). Patch this
       window AND same-origin parent/top directly. */
    function patchPostMessage(win, label) {{
        if (!win) return;
        try {{
            var orig = win.postMessage.bind(win);
            win.postMessage = function(message, targetOrigin, transfer) {{
                if (typeof targetOrigin === 'string' && targetOrigin.indexOf(UPSTREAM_ORIGIN) === 0) {{
                    var dest = (win.location && win.location.origin) || window.location.origin;
                    console.log('[SLACK SHIM] postMessage(' + label + ') ' + targetOrigin + ' -> ' + dest);
                    targetOrigin = dest;
                }}
                if (arguments.length > 2) return orig(message, targetOrigin, transfer);
                return orig(message, targetOrigin);
            }};
        }} catch (e) {{
            console.warn('[SLACK SHIM] postMessage patch failed for ' + label, e);
        }}
    }}
    try {{
        var _pmProto = Window.prototype.postMessage;
        Window.prototype.postMessage = function(message, targetOrigin, transfer) {{
            if (typeof targetOrigin === 'string' && targetOrigin.indexOf(UPSTREAM_ORIGIN) === 0) {{
                var dest = window.location.origin;
                try {{ if (this && this.location) dest = this.location.origin; }} catch (e) {{}}
                console.log('[SLACK SHIM] postMessage(proto) ' + targetOrigin + ' -> ' + dest);
                targetOrigin = dest;
            }}
            if (arguments.length > 2) return _pmProto.call(this, message, targetOrigin, transfer);
            return _pmProto.call(this, message, targetOrigin);
        }};
    }} catch (e) {{}}
    patchPostMessage(window, 'self');
    try {{ if (window.parent && window.parent !== window) patchPostMessage(window.parent, 'parent'); }} catch (e) {{}}
    try {{ if (window.top && window.top !== window) patchPostMessage(window.top, 'top'); }} catch (e) {{}}

    /* Receivers check event.origin === https://app.slack.com (and often
       event instanceof MessageEvent). postMessage now delivers, but the
       parent still timed out — spoof origin via a real MessageEvent, and
       also wrap window.onmessage (not only addEventListener). */
    function spoofMessageEvent(event) {{
        if (!event || event.origin !== window.location.origin) return event;
        try {{
            return new MessageEvent('message', {{
                data: event.data,
                origin: UPSTREAM_ORIGIN,
                lastEventId: event.lastEventId || '',
                source: event.source,
                ports: event.ports ? Array.prototype.slice.call(event.ports) : []
            }});
        }} catch (e) {{
            try {{
                Object.defineProperty(event, 'origin', {{
                    get: function() {{ return UPSTREAM_ORIGIN; }},
                    configurable: true
                }});
                return event;
            }} catch (e2) {{
                return {{
                    data: event.data,
                    origin: UPSTREAM_ORIGIN,
                    source: event.source,
                    ports: event.ports,
                    lastEventId: event.lastEventId,
                    type: 'message'
                }};
            }}
        }}
    }}
    try {{
        var _ael = EventTarget.prototype.addEventListener;
        EventTarget.prototype.addEventListener = function(type, listener, options) {{
            if (type === 'message' && typeof listener === 'function') {{
                var wrapped = function(event) {{
                    var ev = spoofMessageEvent(event);
                    if (ev !== event) {{
                        console.log('[SLACK SHIM] message origin spoofed for listener');
                    }}
                    return listener.call(this, ev);
                }};
                return _ael.call(this, type, wrapped, options);
            }}
            return _ael.call(this, type, listener, options);
        }};
    }} catch (e) {{}}
    try {{
        var _onMsgDesc = Object.getOwnPropertyDescriptor(Window.prototype, 'onmessage');
        if (_onMsgDesc && _onMsgDesc.set) {{
            Object.defineProperty(window, 'onmessage', {{
                configurable: true,
                enumerable: true,
                get: function() {{ return this.__ps_onmessage; }},
                set: function(fn) {{
                    this.__ps_onmessage = fn;
                    if (typeof fn === 'function') {{
                        _onMsgDesc.set.call(this, function(event) {{
                            return fn.call(this, spoofMessageEvent(event));
                        }});
                    }} else {{
                        _onMsgDesc.set.call(this, fn);
                    }}
                }}
            }});
        }}
    }} catch (e) {{}}
    /* Capture-phase safety net: if Slack registered before our wrap somehow,
       re-dispatch is too late; at least log what arrives. */
    try {{
        window.addEventListener('message', function(event) {{
            if (event && event.origin === window.location.origin) {{
                console.log('[SLACK SHIM] saw same-origin message; data keys=',
                    event.data && typeof event.data === 'object' ? Object.keys(event.data) : typeof event.data);
            }}
        }}, true);
    }} catch (e) {{}}

    function shouldRewrite(path) {{
        if (!path || typeof path !== 'string' || path.charAt(0) !== '/') return false;
        if (path.indexOf(PROXY_PREFIX) === 0) return false;
        for (var i = 0; i < SLACK_PATHS.length; i++) {{
            if (path === SLACK_PATHS[i] || path.indexOf(SLACK_PATHS[i]) === 0) return true;
        }}
        return false;
    }}

    function withTenant(url) {{
        if (!PS_TENANT) return url;
        if (url.indexOf('_ps_tenant=') !== -1) return url;
        return url + (url.indexOf('?') >= 0 ? '&' : '?') + '_ps_tenant=' + encodeURIComponent(PS_TENANT);
    }}

    function rewriteUrl(url) {{
        if (typeof url !== 'string' || !url) return url;
        var path = url;
        try {{
            if (url.charAt(0) !== '/') {{
                var parsed = new URL(url, window.location.origin);
                if (parsed.origin !== window.location.origin) return url;
                path = parsed.pathname + parsed.search + parsed.hash;
            }}
        }} catch (e) {{ return url; }}
        if (shouldRewrite(path)) {{
            var rewritten = withTenant(PROXY_PREFIX + path);
            console.log('[SLACK SHIM] proxy-relay rewrite ' + url + ' -> ' + rewritten);
            return rewritten;
        }}
        return url;
    }}

    var _f = window.fetch;
    window.fetch = function(input, init) {{
        if (typeof input === 'string') {{
            input = rewriteUrl(input);
        }} else if (input && input.url) {{
            var rw = rewriteUrl(input.url);
            if (rw !== input.url) {{ try {{ input = new Request(rw, input); }} catch (e) {{}} }}
        }}
        return _f.call(this, input, init);
    }};

    var _xo = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {{
        var args = Array.prototype.slice.call(arguments);
        args[1] = rewriteUrl(url);
        return _xo.apply(this, args);
    }};

    try {{
        var _srcDesc = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'src');
        if (_srcDesc && _srcDesc.set) {{
            Object.defineProperty(HTMLIFrameElement.prototype, 'src', {{
                get: _srcDesc.get,
                set: function(v) {{ _srcDesc.set.call(this, rewriteUrl(String(v || ''))); }},
                configurable: true
            }});
        }}
    }} catch (e) {{}}

    try {{
        var _hrefDesc = Object.getOwnPropertyDescriptor(Location.prototype, 'href');
        if (_hrefDesc && _hrefDesc.set) {{
            Object.defineProperty(Location.prototype, 'href', {{
                get: _hrefDesc.get,
                set: function(v) {{ _hrefDesc.set.call(this, rewriteUrl(String(v || ''))); }},
                configurable: true
            }});
        }}
        var _assign = Location.prototype.assign;
        Location.prototype.assign = function(v) {{ return _assign.call(this, rewriteUrl(String(v || ''))); }};
        var _replace = Location.prototype.replace;
        Location.prototype.replace = function(v) {{ return _replace.call(this, rewriteUrl(String(v || ''))); }};
    }} catch (e) {{}}

    console.log('[SLACK SHIM] Installed proxy-relay + postMessage bridge. Proxy prefix: ' + PROXY_PREFIX);
}})();
</script>
"""
