# HubSpot Passthrough — Full Source for Shela

**Date:** 2026-06-27  
**From:** Michael  
**Status:** Uncommitted local changes (weekend review — no repo access needed)

---

## Problem

PolySniffer passthrough for HubSpot (endpoint 4, `app-na2.hubspot.com`) loads login HTML (~46KB, HTTP 200) but HubSpot LoginUI shows:

> **This login URL is invalid.**

That text is **not** in the server HTML — LoginUI injects it client-side. LoginUI bundle maps it to error code `MISSING_FRAGMENTS` (OAuth hash-fragment routing).

## What works now

- **Stop capture** — clears session mode; no auto-restart loop
- **Open in new tab** — opens `/pt/polysniff/4/login/` (raw passthrough, not workspace shell)

## Still broken

- HubSpot login form in workspace embed and in new tab (same error)
- Location spoof runs in **workspace embed only** (not yet in standalone `/pt/polysniff/` pages)

## Script execution order (workspace passthrough)

1. `sniff_pt_embed.build_workspace_shell_guard_script` — `history.replaceState` to `/pt/polysniff/4/login/`
2. `HubspotPassthroughHandler.polysniffer_workspace_location_spoof_script` — patches `location`, `document.URL`
3. HubSpot HTML + `get_client_side_shim` — fetch/XHR rewrite; re-applies spoof if flag set

## Suggested next fix

Inject `_hubspot_location_spoof_iife` at the start of `get_client_side_shim()` so `/pt/polysniff/4/login/` gets the same spoof.

---

## File 1 of 4: hubspot_handler.py

Repo path: `dose/passthrough/handlers/hubspot_handler.py`

```python
# dose/passthrough/handlers/hubspot_handler.py
"""
HubSpot passthrough — proxy app.hubspot.com inside PolySaaS admin shell.

Track A of HubSpot integration. API/OAuth for User Context Manager is separate.
"""
from __future__ import annotations

import json
import logging
import re
from urllib.parse import urlparse

from django.http import HttpResponse

from dose.passthrough.handlers.handler_base import PassthroughHandlerBase, proxy_prefix_for_trigger_endpoint
from dose.polysniffer.handlers.hubspot_bases import (
    discover_origins_from_text,
    global_entry_path,
    load_known_bases,
    load_session_landing_path,
    preferred_upstream_origin,
    remember_bases,
    remember_from_location,
    remember_landing_from_location,
    remember_landing_path,
    resolve_hubspot_browse_subpath,
    rewrite_location_through_proxy,
)

logger = logging.getLogger(__name__)

_HUBSPOT_HOST_MARKERS = ('hubspot.com', 'hubspot.net')

_HUBSPOT_GLOBAL_ENTRY = "/login/"

_BYPASS_PREFIXES = (
    '/api/',
    '/hs/',
    '/hublytics/',
    '/static/',
    '/notifications/',
    '/filemanager/',
    '/webpack/',
    '/webhooks/',
)

_PROXY_PATH_PREFIXES = (
    '/contacts/',
    '/companies/',
    '/deals/',
    '/service/',
    '/tickets/',
    '/reports/',
    '/settings/',
    '/marketing/',
    '/sales/',
    '/cms/',
    '/preferences/',
    '/home/',
    '/login/',
    '/oauth/',
    '/account/',
    '/user-guide/',
    '/notifications/',
    '/calling/',
    '/payments/',
    '/commerce/',
    '/social/',
    '/ads/',
    '/email/',
    '/automation/',
    '/workflows/',
    '/lists/',
    '/sequences/',
    '/forecasting/',
    '/dashboard/',
    '/global-home/',
    '/objects/',
)


class HubspotPassthroughHandler(PassthroughHandlerBase):
    """HubSpot web UI passthrough."""

    _DJANGO_COOKIE_NAMES = frozenset({
        'sessionid', 'csrftoken', 'messages', 'django_language',
    })

    @classmethod
    def matches_endpoint(cls, endpoint) -> bool:
        blob = ' '.join([
            str(getattr(endpoint, 'endpoint_url', '') or ''),
            str(getattr(endpoint, 'slug', '') or ''),
            str(getattr(endpoint, 'description', '') or ''),
        ]).lower()
        return 'hubspot' in blob or any(m in blob for m in _HUBSPOT_HOST_MARKERS)

    def should_wrap_in_admin_template(self, request, upstream_path, **kwargs) -> bool:
        low = (upstream_path or '').lower()
        if any(low.startswith(p) for p in _BYPASS_PREFIXES):
            return False
        if self._is_static_asset(low):
            return False
        return True

    def should_process_html_response(self, request, upstream_path, **kwargs) -> bool:
        low = (upstream_path or '').lower()
        if any(low.startswith(p) for p in _BYPASS_PREFIXES):
            return False
        if self._is_static_asset(low):
            return False
        return True

    def filter_cookies_for_upstream(self, request, cookies: dict) -> dict:
        return {k: v for k, v in cookies.items() if k not in self._DJANGO_COOKIE_NAMES}

    def get_upstream_cookies(self, request) -> dict:
        """Return HubSpot session cookies if available from browser (Track A passthrough)."""
        self._bind_hubspot_request(request)
        try:
            cookies = self.filter_cookies_for_upstream(request, dict(request.COOKIES))
            if cookies:
                return cookies
        except Exception:
            pass
        return {}

    def augment_outbound_headers(self, request, headers, target_url: str) -> None:
        """Attach API token for proxied api.hubapi.com calls when tenant is connected."""
        if 'api.hubapi.com' not in (target_url or ''):
            return
        try:
            from dose.utils import get_current_tenant
            from dose.services.hubspot_oauth import get_tenant_hubspot_app

            tenant = getattr(request, 'tenant', None) or get_current_tenant(request)
            ta = get_tenant_hubspot_app(tenant) if tenant else None
            token = (ta.extra_config or {}).get('hs_access_token') if ta else None
            if token:
                headers['Authorization'] = f'Bearer {token}'
        except Exception as exc:
            logger.debug('[HubSpotHandler] augment_outbound_headers: %s', exc)

    def _endpoint_id(self, request) -> int | None:
        eid = getattr(request, '_polysniffer_endpoint_id', None)
        if eid is not None:
            try:
                return int(eid)
            except (TypeError, ValueError):
                pass
        endpoint = getattr(request, '_passthrough_endpoint', None) or self.endpoint
        return int(endpoint.pk) if endpoint is not None and getattr(endpoint, 'pk', None) else None

    def _effective_proxy_prefix(self, request, endpoint, endpoint_url: str | None = None) -> str:
        pub = (getattr(request, '_polysniffer_proxy_prefix', None) or '').strip()
        if pub:
            return pub.rstrip('/')
        if endpoint is not None:
            return proxy_prefix_for_trigger_endpoint(endpoint).rstrip('/')
        return self._proxy_prefix_from_url(endpoint_url or '').rstrip('/')

    def _known_bases(self, request, endpoint_url: str) -> set[str]:
        return load_known_bases(request, self._endpoint_id(request), endpoint_url or '')

    def should_follow_upstream_redirects(self, request, target_url: str, upstream_path: str) -> bool:
        """Allow fetch_upstream_index_html to follow redirects internally so the final HTML (e.g., login page) is embedded."""
        return True

    @staticmethod
    def _bind_hubspot_request(request) -> None:
        try:
            from dose.polysniffer.handlers.hubspot_bases import bind_hubspot_passthrough_request
            bind_hubspot_passthrough_request(request)
        except Exception:
            pass

    def passthrough_early_shell_paths(self):
        """Global DB entry paths — redirect to session landing when known."""
        return ("/", "/login", "/login/")

    def try_root_display_shell_response(self, request, endpoint, url_trigger_segment):
        """
        When session has a post-login landing, skip global /login/ and open the workspace directly.
        """
        self._bind_hubspot_request(request)
        endpoint_id = self._endpoint_id(request)
        landing = load_session_landing_path(request, endpoint_id)
        if not landing:
            return None
        endpoint_url = getattr(endpoint, "endpoint_url", None) or "https://app.hubspot.com"
        proxy_prefix = self._effective_proxy_prefix(request, endpoint or self.endpoint, endpoint_url)
        from django.http import HttpResponseRedirect

        dest = proxy_prefix.rstrip("/") + landing
        logger.info("[HubSpot] session landing redirect -> %s", dest)
        return HttpResponseRedirect(dest)

    def resolve_workspace_browse_subpath(self, request, endpoint) -> str:
        return resolve_hubspot_browse_subpath(request, endpoint, self._endpoint_id(request))

    def upstream_url_for_subpath(self, endpoint_url, clean_path):
        try:
            from dose.polysniffer.handlers.hubspot_bases import get_hubspot_passthrough_request
            req = get_hubspot_passthrough_request()
        except Exception:
            req = None
        endpoint_id = self._endpoint_id(req) if req else None
        if endpoint_id is None and self.endpoint is not None:
            endpoint_id = getattr(self.endpoint, "pk", None)
        origin = preferred_upstream_origin(req, endpoint_id, endpoint_url or "")
        if not origin:
            return None
        path = clean_path if (clean_path or "").startswith("/") else f"/{clean_path or ''}"
        return f"{origin.rstrip('/')}{path}"

    def postprocess_upstream_response(self, resp, request, **context):
        self._bind_hubspot_request(request)
        endpoint_url = context.get('endpoint_url') or ''
        endpoint_id = self._endpoint_id(request)
        proxy_prefix = self._effective_proxy_prefix(
            request,
            getattr(request, '_passthrough_endpoint', None) or self.endpoint,
            endpoint_url,
        )
        known = self._known_bases(request, endpoint_url)

        for hop in getattr(resp, 'history', None) or ():
            remember_from_location(request, endpoint_id, hop.headers.get('Location', ''))
            if hop.url:
                remember_bases(request, endpoint_id, discover_origins_from_text(hop.url))
                remember_landing_from_location(request, endpoint_id, hop.url)

        upstream_path = context.get('upstream_path') or ''
        if resp.status_code == 200 and upstream_path:
            remember_landing_path(request, endpoint_id, upstream_path)

        if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get('Location', '')
            remember_from_location(request, endpoint_id, location)
            rewritten = rewrite_location_through_proxy(location, proxy_prefix, known)
            if rewritten != location:
                logger.info('[HubSpot] redirect %s -> %s', location, rewritten)
                redirect = HttpResponse(status=resp.status_code)
                redirect['Location'] = rewritten
                for name, value in resp.headers.items():
                    if name.lower() == 'set-cookie':
                        redirect[name] = value
                return redirect
        return resp

    def polysniffer_non_page_path_prefixes(self, request):
        """HAR-derived API/asset families — see direct HAR and _BYPASS_PREFIXES."""
        return _BYPASS_PREFIXES

    def polysniffer_workspace_browse_subpath(self, endpoint, request=None):
        """
        PolySniffer workspace HTML entry: session landing path, else global /login/.
        DB starting_uri is the global startpoint only — not the post-login float.
        """
        if request is not None:
            return resolve_hubspot_browse_subpath(request, endpoint, self._endpoint_id(request))
        uri = (getattr(endpoint, "starting_uri", None) or "").strip()
        if uri:
            return uri if uri.startswith("/") else f"/{uri}"
        return _HUBSPOT_GLOBAL_ENTRY

    @staticmethod
    def _canonical_host_from_bases(endpoint_url: str, known_bases: list[str] | None = None) -> str:
        host = urlparse((endpoint_url or "").strip()).netloc or ""
        if host and ("hubspot.com" in host.lower()):
            return host.split(":")[0]
        for origin in known_bases or []:
            parsed = urlparse(origin)
            if parsed.netloc and "hubspot.com" in parsed.netloc.lower():
                return parsed.netloc.split(":")[0]
        return "app.hubspot.com"

    @classmethod
    def _hubspot_location_spoof_iife(
        cls,
        proxy_prefix: str,
        shell_prefix: str = "",
        canonical_host: str = "app.hubspot.com",
    ) -> str:
        proxy = json.dumps((proxy_prefix or "").rstrip("/"))
        shell = json.dumps((shell_prefix or "").rstrip("/"))
        host = json.dumps((canonical_host or "app.hubspot.com").split(":")[0])
        return f"""(function() {{
  var PROXY_PREFIX = {proxy};
  var SHELL_PREFIX = {shell};
  var CANONICAL_HOST = {host};
  var CANONICAL_ORIGIN = 'https://' + CANONICAL_HOST;
  window.__PS_HUBSPOT_LOCATION_SPOOF = true;
  if (!window.__PS_REAL_ORIGIN) {{
    window.__PS_REAL_ORIGIN = window.location.protocol + '//' + window.location.host;
  }}
  var _realPathname = null;
  var _realHref = null;
  var _setHref = null;
  function normalizeSubpath(path) {{
    var p = path || '/';
    if (!p || p.charAt(0) !== '/') p = '/' + p;
    if (SHELL_PREFIX && p.indexOf(SHELL_PREFIX) === 0) {{
      p = p.slice(SHELL_PREFIX.length) || '/';
      if (!p || p.charAt(0) !== '/') p = '/' + p;
    }}
    var shellMatch = p.match(/^\\/dose\\/sniff\\/\\d+\\/workspace(\\/.*)?$/);
    if (shellMatch) {{
      p = shellMatch[1] || '/';
      if (!p || p.charAt(0) !== '/') p = '/' + p;
    }}
    if (/^\\/(passthrough|native)(\\/|$)/.test(p)) {{
      p = p.replace(/^\\/(passthrough|native)/, '') || '/';
      if (!p || p.charAt(0) !== '/') p = '/' + p;
    }}
    if (PROXY_PREFIX && p.indexOf(PROXY_PREFIX) === 0) {{
      p = p.slice(PROXY_PREFIX.length) || '/';
    }}
    var adminMatch = p.match(/^\\/pt\\/admin\\/[^/]+(\\/.*)?$/);
    if (adminMatch) {{
      p = adminMatch[1] || '/';
    }}
    if (!p || p.charAt(0) !== '/') p = '/' + p;
    if (p.toLowerCase().indexOf('/login') === 0 && p.slice(-1) !== '/') p += '/';
    return p;
  }}
  function upstreamPathname(raw) {{
    try {{
      var actual = raw;
      if (actual == null) actual = _realPathname ? _realPathname() : '/login/';
      return normalizeSubpath(actual || '/');
    }} catch (e) {{ return '/login/'; }}
  }}
  function upstreamHref(rawHref) {{
    try {{
      var actual = rawHref;
      if (actual == null) actual = _realHref ? _realHref() : '/login/';
      var u = new URL(String(actual || '/'), window.__PS_REAL_ORIGIN || window.location.href);
      u.protocol = 'https:';
      u.hostname = CANONICAL_HOST;
      u.port = '';
      u.pathname = upstreamPathname(u.pathname);
      return u.toString();
    }} catch (e2) {{ return CANONICAL_ORIGIN + upstreamPathname('/login/'); }}
  }}
  function proxyHrefFromUpstream(value) {{
    var raw = String(value || '');
    if (!raw) return raw;
    try {{
      var parsed = new URL(raw, CANONICAL_ORIGIN);
      if (parsed.hostname === CANONICAL_HOST || parsed.hostname.indexOf('app-') === 0 || parsed.hostname === 'local.hubspot.com') {{
        var sub = parsed.pathname + (parsed.search || '') + (parsed.hash || '');
        if (!sub || sub.charAt(0) !== '/') sub = '/' + sub;
        if (PROXY_PREFIX) return PROXY_PREFIX + sub;
      }}
    }} catch (e3) {{}}
    return raw;
  }}
  function applyHubspotLocationSpoof() {{
    try {{
      var hrefDesc = Object.getOwnPropertyDescriptor(window.Location.prototype, 'href');
      var pathnameDesc = Object.getOwnPropertyDescriptor(window.Location.prototype, 'pathname');
      var hostnameDesc = Object.getOwnPropertyDescriptor(window.Location.prototype, 'hostname');
      var hostDesc = Object.getOwnPropertyDescriptor(window.Location.prototype, 'host');
      var originDesc = Object.getOwnPropertyDescriptor(window.Location.prototype, 'origin');
      var protocolDesc = Object.getOwnPropertyDescriptor(window.Location.prototype, 'protocol');
      if (!_realPathname && pathnameDesc && pathnameDesc.get) {{
        _realPathname = pathnameDesc.get.bind(window.location);
      }}
      if (!_realHref && hrefDesc && hrefDesc.get) {{
        _realHref = hrefDesc.get.bind(window.location);
      }}
      if (!_setHref && hrefDesc && hrefDesc.set) {{
        _setHref = hrefDesc.set.bind(window.location);
      }}
      if (pathnameDesc && pathnameDesc.get) {{
        Object.defineProperty(window.Location.prototype, 'pathname', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return upstreamPathname(); }},
          set: pathnameDesc.set
        }});
      }}
      if (hostnameDesc && hostnameDesc.get) {{
        Object.defineProperty(window.Location.prototype, 'hostname', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return CANONICAL_HOST; }},
          set: hostnameDesc.set
        }});
      }}
      if (hostDesc && hostDesc.get) {{
        Object.defineProperty(window.Location.prototype, 'host', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return CANONICAL_HOST; }},
          set: hostDesc.set
        }});
      }}
      if (originDesc && originDesc.get) {{
        Object.defineProperty(window.Location.prototype, 'origin', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return CANONICAL_ORIGIN; }},
          set: originDesc.set
        }});
      }}
      if (protocolDesc && protocolDesc.get) {{
        Object.defineProperty(window.Location.prototype, 'protocol', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return 'https:'; }},
          set: protocolDesc.set
        }});
      }}
      if (hrefDesc && hrefDesc.get && _setHref) {{
        Object.defineProperty(window.Location.prototype, 'href', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return upstreamHref(); }},
          set: function(v) {{ return _setHref(proxyHrefFromUpstream(v)); }}
        }});
        Object.defineProperty(window.location, 'href', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return upstreamHref(); }},
          set: function(v) {{ return _setHref(proxyHrefFromUpstream(v)); }}
        }});
      }}
      window.Location.prototype.toString = function() {{ return upstreamHref(); }};
      try {{
        var docUrlDesc = Object.getOwnPropertyDescriptor(Document.prototype, 'URL');
        if (docUrlDesc && docUrlDesc.get) {{
          Object.defineProperty(document, 'URL', {{
            configurable: true,
            enumerable: true,
            get: function() {{ return upstreamHref(); }}
          }});
        }}
      }} catch (eDoc) {{}}
      try {{
        var docUriDesc = Object.getOwnPropertyDescriptor(Document.prototype, 'documentURI');
        if (docUriDesc && docUriDesc.get) {{
          Object.defineProperty(document, 'documentURI', {{
            configurable: true,
            enumerable: true,
            get: function() {{ return upstreamHref(); }}
          }});
        }}
      }} catch (eUri) {{}}
      console.log('[PolySaaS HS] location spoof', upstreamHref(), 'real=', _realHref ? _realHref() : '?');
    }} catch (e) {{
      console.warn('[PolySaaS HS] location spoof failed', e);
    }}
  }}
  window.__PS_HUBSPOT_REAPPLY_SPOOF = applyHubspotLocationSpoof;
  applyHubspotLocationSpoof();
}})();"""

    def polysniffer_workspace_location_spoof_script(
        self,
        proxy_prefix: str,
        shell_prefix: str = "",
        canonical_host: str = "",
    ) -> str:
        """
        HubSpot login SPA validates window.location against app*.hubspot.com/login/.
        PolySniffer workspace URLs must be stripped before upstream scripts boot.
        """
        host = canonical_host or self._canonical_host_from_bases(
            getattr(self.endpoint, "endpoint_url", "") if self.endpoint else "",
        )
        body = self._hubspot_location_spoof_iife(proxy_prefix, shell_prefix, host)
        return f'<script data-hubspot-location-spoof="1">{body}</script>'

    def get_client_side_shim(self, proxy_prefix: str, known_bases: list[str]) -> str:
        bases_js = json.dumps(known_bases)
        return f"""
<script data-hubspot-pt-shim="1">
(function() {{
  var PROXY_PREFIX = {json.dumps(proxy_prefix.rstrip('/'))};
  var KNOWN_BASES = {bases_js};
  function isAppHost(host) {{
    if (!host) return false;
    host = host.toLowerCase().split(':')[0];
    if (host.indexOf('static.hsappstatic.net') >= 0) return false;
    return host === 'app.hubspot.com' || host.indexOf('app-') === 0 || host === 'local.hubspot.com';
  }}
  function rememberOrigin(origin) {{
    if (!origin || KNOWN_BASES.indexOf(origin) >= 0) return;
    if (isAppHost(origin.replace(/^https?:\\/\\//, ''))) KNOWN_BASES.push(origin);
  }}
  function isAssetPath(path) {{
    var low = (path || '').toLowerCase();
    return low.indexOf('/api/') === 0 || low.indexOf('/hs/') === 0 || low.indexOf('/static/') === 0 ||
      low.indexOf('/webpack/') === 0 || low.indexOf('/hublytics/') === 0 || low.indexOf('/notifications/') === 0;
  }}
  function workspaceNavUrl(url) {{
    var shell = window.__PS_WORKSPACE_SHELL_PREFIX || '';
    if (!shell) return url;
    try {{
      var parsed = new URL(url, window.__PS_REAL_ORIGIN || window.location.origin);
      var realOrigin = window.__PS_REAL_ORIGIN || window.location.origin;
      if (parsed.origin !== realOrigin) return url;
      if (parsed.pathname.indexOf(PROXY_PREFIX) !== 0) return url;
      var sub = parsed.pathname.slice(PROXY_PREFIX.length) || '/';
      if (!sub || sub.charAt(0) !== '/') sub = '/' + sub;
      if (isAssetPath(sub)) return url;
      return shell + sub + (parsed.search || '') + (parsed.hash || '');
    }} catch (e) {{}}
    return url;
  }}
  function rewriteUrl(url) {{
    if (!url || url.indexOf(PROXY_PREFIX) === 0) return url;
    try {{
      var parsed = new URL(url, window.__PS_REAL_ORIGIN || window.location.origin);
      if (isAppHost(parsed.hostname)) {{
        rememberOrigin(parsed.origin);
        return PROXY_PREFIX + parsed.pathname + (parsed.search || '') + (parsed.hash || '');
      }}
      var realOrigin = window.__PS_REAL_ORIGIN || window.location.origin;
      if (parsed.origin === realOrigin) {{
        var path = parsed.pathname + (parsed.search || '');
        if (path.indexOf(PROXY_PREFIX) === 0) return url;
        if (path.charAt(0) === '/' && path.indexOf('/admin/') !== 0 && path.indexOf('/dose/') !== 0) {{
          var low = path.toLowerCase();
          if (low.indexOf('/api/') === 0 || low.indexOf('/hs/') === 0 || low.indexOf('/global-home/') === 0 ||
              low.indexOf('/home') === 0 || low.indexOf('/login') === 0 || low.indexOf('/oauth') === 0) {{
            return PROXY_PREFIX + path + (parsed.hash || '');
          }}
        }}
      }}
      for (var i = 0; i < KNOWN_BASES.length; i++) {{
        var base = KNOWN_BASES[i];
        if (url.indexOf(base) === 0) {{
          return PROXY_PREFIX + url.slice(base.length);
        }}
      }}
    }} catch (e) {{}}
    return url;
  }}
  var _fetch = window.fetch;
  window.fetch = function(input, init) {{
    if (typeof input === 'string') input = rewriteUrl(input);
    else if (input && input.url) {{
      var u = rewriteUrl(input.url);
      if (u !== input.url) input = new Request(u, input);
    }}
    return _fetch.apply(this, arguments);
  }};
  var _open = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function(method, url) {{
    arguments[1] = rewriteUrl(url);
    return _open.apply(this, arguments);
  }};
  function navigate(url) {{
    var u = workspaceNavUrl(rewriteUrl(String(url || '')));
    if (u) window.location.assign(u);
  }}
  var _assign = window.location.assign.bind(window.location);
  var _replace = window.location.replace.bind(window.location);
  window.location.assign = function(url) {{ _assign(workspaceNavUrl(rewriteUrl(String(url)))); }};
  window.location.replace = function(url) {{ _replace(workspaceNavUrl(rewriteUrl(String(url)))); }};
  if (!window.__PS_HUBSPOT_LOCATION_SPOOF) {{
    try {{
      var _hrefDesc = Object.getOwnPropertyDescriptor(window.Location.prototype, 'href');
      if (_hrefDesc && _hrefDesc.set) {{
        Object.defineProperty(window.location, 'href', {{
          configurable: true,
          get: function() {{ return _hrefDesc.get.call(window.location); }},
          set: function(v) {{ _hrefDesc.set.call(window.location, workspaceNavUrl(rewriteUrl(String(v)))); }}
        }});
      }}
    }} catch (e) {{}}
  }} else if (window.__PS_HUBSPOT_REAPPLY_SPOOF) {{
    window.__PS_HUBSPOT_REAPPLY_SPOOF();
  }}
  document.addEventListener('click', function(ev) {{
    var el = ev.target;
    var a = el && el.closest ? el.closest('a[href]') : null;
    if (!a) return;
    var tgt = (a.getAttribute('target') || '').toLowerCase();
    if (tgt === '_top' || tgt === '_parent') {{
      ev.preventDefault();
      navigate(a.href || a.getAttribute('href'));
    }}
  }}, true);
  document.addEventListener('submit', function(ev) {{
    var form = ev.target;
    if (!form || !form.getAttribute) return;
    var tgt = (form.getAttribute('target') || '').toLowerCase();
    if (tgt === '_top' || tgt === '_parent') {{
      form.setAttribute('target', '_self');
      if (form.action) form.action = rewriteUrl(form.action);
    }}
  }}, true);
}})();
</script>
"""

    def process_html_response(self, html_str, request, endpoint_url=None, **context):
        self._bind_hubspot_request(request)
        if not html_str:
            return html_str
        from dose.polysniffer.handlers.hubspot_native_sniff import _rewrite_hubspot_native_html

        endpoint = getattr(request, '_passthrough_endpoint', None) or self.endpoint
        endpoint_url = endpoint_url or getattr(endpoint, 'endpoint_url', '') or ''
        prefix = self._effective_proxy_prefix(request, endpoint, endpoint_url)
        base = self._base_from_url(endpoint_url)
        endpoint_id = self._endpoint_id(request)
        known = self._known_bases(request, endpoint_url)
        html = _rewrite_hubspot_native_html(
            html_str,
            base_origin=base,
            proxy_prefix=prefix,
            handler=self,
            known_bases=known,
            request=request,
            endpoint_id=endpoint_id,
        )
        shim = self.get_client_side_shim(prefix, sorted(known))
        if 'data-hubspot-pt-shim="1"' not in html:
            if re.search(r'(?i)<head[^>]*>', html):
                html = re.sub(r'(?i)(<head[^>]*>)', r'\1' + shim, html, count=1)
            else:
                html = shim + html
        return html

    @staticmethod
    def _proxy_prefix_from_url(endpoint_url: str) -> str:
        if not endpoint_url:
            return '/pt/admin/app.hubspot.com/'
        host = urlparse(endpoint_url).netloc or 'app.hubspot.com'
        return f'/pt/admin/{host}/'

    @staticmethod
    def _base_from_url(endpoint_url: str) -> str:
        if not endpoint_url:
            return 'https://app.hubspot.com'
        p = urlparse(endpoint_url)
        return f'{p.scheme}://{p.netloc}'

    @staticmethod
    def _is_static_asset(path: str) -> bool:
        return bool(re.search(r'\.(js|css|map|png|jpg|jpeg|gif|svg|ico|woff2?|ttf|json)(\?|$)', path, re.I))

    def _rewrite_html(self, html: str, proxy_prefix: str, base: str) -> str:
        prefix = proxy_prefix.rstrip('/')
        bases = {base.rstrip('/')}
        if 'app.hubspot.com' in base:
            bases.add('https://app.hubspot.com')
            bases.add('http://app.hubspot.com')

        for b in bases:
            html = html.replace(f'"{b}/', f'"{prefix}/')
            html = html.replace(f"'{b}/", f"'{prefix}/")

        def _abs_repl(match):
            path = match.group(1)
            if path.startswith('//') or ':' in path[:12]:
                return match.group(0)
            if not self._should_proxy_path(path, prefix):
                return match.group(0)
            return f'"{prefix}{path}"'

        html = re.sub(r'"(/[^"\\s#?][^"]*)"', _abs_repl, html)
        return html

    def _should_proxy_path(self, path: str, proxy_prefix: str) -> bool:
        if not path or not path.startswith('/'):
            return False
        if path.startswith(proxy_prefix):
            return False
        low = path.lower()
        if any(low.startswith(p) for p in _BYPASS_PREFIXES):
            return False
        return any(low.startswith(p) for p in _PROXY_PATH_PREFIXES) or low in ('/', '/home', '/home/')


# Register PolySniffer native sniff processor when handler module loads.
import dose.polysniffer.handlers.hubspot_native_sniff  # noqa: F401,E402

```

## File 2 of 4: sniff_pt_embed.py

Repo path: `dose/polysniffer/sniff_pt_embed.py`

```python
"""
Inline passthrough embed for PolySniffer workspace.

Browser-facing prefix: /pt/polysniff/{endpoint_id}/ (not /pt/admin/).
Production handlers run internally via dispatch_polysniff_passthrough (frozen sniff_pt_proxy).
"""
from __future__ import annotations

import json
import re
from urllib.parse import urlparse

from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from dose.passthrough.embed_fragments import build_scoped_embed_fragments
from dose.passthrough.registry import resolve_handler_for_pt_admin_trigger
from dose.polysniffer.handler_hooks import non_page_path_prefixes
from dose.polysniffer.sniff_native_embed import (
    _is_html_response,
    _split_head_for_inline,
    workspace_shell_prefix,
)
from dose.polysniffer.sniff_pt_proxy import public_polysniff_prefix
from dose.polysniffer.workspace_pt_redirect import (
    rewrite_pt_form_actions_to_workspace,
    subpath_from_passthrough_location,
    workspace_shell_url,
)


def polysniff_proxy_prefix(endpoint_id: int) -> str:
    """Public PolySniffer passthrough prefix — /pt/polysniff/<id>."""
    return public_polysniff_prefix(endpoint_id).rstrip("/")


def build_workspace_shell_guard_script(
    shell_prefix: str,
    proxy_prefix: str,
    endpoint_id: int,
    *,
    non_page_prefixes: tuple[str, ...] = (),
) -> str:
    """Keep passthrough HTML navigations inside the PolySniffer workspace shell."""
    shell = json.dumps((shell_prefix or "").rstrip("/"))
    proxy = json.dumps((proxy_prefix or "").rstrip("/"))
    prefixes = json.dumps(list(non_page_prefixes))
    ep = int(endpoint_id)
    return f"""<script data-ps-workspace-guard="1">
(function() {{
  var SHELL = {shell};
  var PROXY = {proxy};
  var EP = {ep};
  var NON_PAGE = {prefixes};
  // HubSpot login SPA treats /dose/sniff/.../workspace/login as an invalid magic-link path.
  // Present /pt/polysniff/<id>/login/ to the browser before upstream scripts boot.
  try {{
    var p = window.location.pathname || '';
    if (PROXY && p.indexOf('/dose/sniff/') >= 0 && p.indexOf('/workspace/') >= 0) {{
      var tail = p.split('/workspace/')[1] || 'login/';
      if (tail.charAt(0) === '/') tail = tail.slice(1);
      if (tail.toLowerCase().indexOf('login') === 0 && tail.slice(-1) !== '/') tail += '/';
      history.replaceState(null, '', PROXY + '/' + tail + window.location.search + window.location.hash);
    }}
  }} catch (e) {{}}
  function isNonPage(sub) {{
    var low = (sub || '').toLowerCase();
    if (!low || low.charAt(0) !== '/') low = '/' + (low || '');
    for (var i = 0; i < NON_PAGE.length; i++) {{
      var p = NON_PAGE[i];
      if (p.charAt(0) !== '/') p = '/' + p;
      if (low.indexOf(p.toLowerCase()) === 0) return true;
    }}
    var last = low.split('/').pop() || '';
    if (last.indexOf('.') > 0) {{
      var ext = last.split('.').pop();
      if (/^(js|css|map|png|jpg|jpeg|gif|svg|ico|woff2?|json)$/.test(ext)) return true;
    }}
    return false;
  }}
  function shellUrl(pathname, search, hash) {{
    if (!PROXY || pathname.indexOf(PROXY) !== 0) return null;
    var sub = pathname.slice(PROXY.length) || '/';
    if (!sub || sub.charAt(0) !== '/') sub = '/' + sub;
    if (isNonPage(sub)) return null;
    return SHELL + sub + (search || '') + (hash || '');
  }}
  function guard(url) {{
    try {{
      var u = new URL(String(url || ''), window.location.origin);
      if (u.origin !== window.location.origin) return url;
      var target = shellUrl(u.pathname, u.search, u.hash);
      if (target) return target;
      if (u.pathname.indexOf('/dose/sniff/' + EP + '/workspace') === 0) return url;
      if (u.pathname.indexOf('/pt/admin/') === 0) {{
        var rest = u.pathname.replace(/^\\/pt\\/admin\\/[^/]+/, '') || '/';
        if (!rest || rest.charAt(0) !== '/') rest = '/' + rest;
        if (!isNonPage(rest)) return SHELL + rest + (u.search || '') + (u.hash || '');
      }}
      var p = u.pathname || '/';
      if (p.indexOf('/pt/') !== 0 && p.indexOf('/admin/') !== 0 && p.indexOf('/dose/') !== 0 &&
          p.indexOf('/accounts/') !== 0 && p.charAt(0) === '/' && !isNonPage(p)) {{
        return SHELL + p + (u.search || '') + (u.hash || '');
      }}
    }} catch (e) {{}}
    return url;
  }}
  var _assign = window.location.assign.bind(window.location);
  var _replace = window.location.replace.bind(window.location);
  window.location.assign = function(u) {{ _assign(guard(u)); }};
  window.location.replace = function(u) {{ _replace(guard(u)); }};
  try {{
    var _href = Object.getOwnPropertyDescriptor(window.Location.prototype, 'href');
    if (_href && _href.set) {{
      Object.defineProperty(window.location, 'href', {{
        configurable: true,
        get: function() {{ return _href.get.call(window.location); }},
        set: function(v) {{ _href.set.call(window.location, guard(v)); }}
      }});
    }}
  }} catch (e) {{}}
  var _push = history.pushState.bind(history);
  var _rep = history.replaceState.bind(history);
  history.pushState = function(state, title, url) {{
    if (url) {{ var g = guard(url); if (g !== url) {{ _push(state, title, g); return; }} }}
    return _push.apply(history, arguments);
  }};
  history.replaceState = function(state, title, url) {{
    if (url) {{ var g = guard(url); if (g !== url) {{ _rep(state, title, g); return; }} }}
    return _rep.apply(history, arguments);
  }};
  window.__PS_WORKSPACE_SHELL_PREFIX = SHELL;
}})();
</script>"""


def _trigger_host(endpoint) -> str:
    from urllib.parse import urlparse

    return urlparse((getattr(endpoint, "endpoint_url", None) or "").strip()).netloc or ""


def build_inline_passthrough_embed_context(
    request,
    endpoint_id: int,
    endpoint,
    path: str,
    *,
    endpoint_label: str = "",
) -> dict | None:
    """Passthrough HTML as inline embed — /pt/polysniff/{id}/ in browser, handler chain internal."""
    from dose.polysniffer.sniff_pt_proxy import dispatch_polysniff_passthrough
    from dose.polysniffer.sniff_tenant import bind_request_tenant, get_sniff_capture_session

    trigger = _trigger_host(endpoint)
    if not trigger:
        return None

    bind_request_tenant(request)
    session = get_sniff_capture_session(request, endpoint_id)
    request._polysniffer_endpoint_id = endpoint_id
    request._polysniffer_sniff_mode = "passthrough"
    request._polysniffer_workspace_inline = True
    if session:
        request._polysniffer_capture = session

    handler = resolve_handler_for_pt_admin_trigger(trigger)
    if handler is not None:
        handler.endpoint = endpoint

    subpath = (path or "").strip().lstrip("/")
    response = dispatch_polysniff_passthrough(request, endpoint_id, subpath)

    if response.status_code in (301, 302, 303, 307, 308):
        loc = response.get("Location", "")
        rel = subpath_from_passthrough_location(loc, endpoint_id, trigger)
        return {"redirect": workspace_shell_url(endpoint_id, rel)}

    if request.method != "GET" or not _is_html_response(response):
        return None
    try:
        raw_html = response.content.decode("utf-8", errors="ignore")
    except Exception:
        return None
    if not raw_html or len(raw_html) < 50:
        return None

    embed_head, scoped_body = build_scoped_embed_fragments(
        raw_html,
        trigger,
        handler=handler,
        request=request,
    )

    head_html = rewrite_pt_form_actions_to_workspace(str(embed_head), endpoint_id, trigger)
    body_html = rewrite_pt_form_actions_to_workspace(str(scoped_body), endpoint_id, trigger)
    head_static, head_scripts = _split_head_for_inline(head_html)
    orch_bar = render_to_string("polysniffer/sniff_pt_orchestration_bar.html", request=request)
    shell_base = workspace_shell_prefix(endpoint_id)
    proxy_base = polysniff_proxy_prefix(endpoint_id)
    np_prefixes = non_page_path_prefixes(handler, request, f"/{subpath}" if subpath else "/")
    guard = build_workspace_shell_guard_script(
        shell_base,
        proxy_base,
        endpoint_id,
        non_page_prefixes=np_prefixes,
    )
    if handler is not None and hasattr(handler, "polysniffer_workspace_location_spoof_script"):
        try:
            canonical_host = urlparse(
                getattr(endpoint, "endpoint_url", "") or "",
            ).netloc.split(":")[0]
            spoof = handler.polysniffer_workspace_location_spoof_script(
                proxy_base,
                shell_base,
                canonical_host=canonical_host,
            )
            if spoof:
                guard = mark_safe(f"{guard}{spoof}")
        except Exception:
            pass
    scoped_base = f'<base href="{proxy_base}/">'
    body_html = re.sub(
        r'(<div class="polysaas-passthrough-scope[^"]*"[^>]*>)',
        r"\1" + scoped_base,
        body_html,
        count=1,
    )
    embed_body = mark_safe(f"{orch_bar}{head_scripts}{body_html}")

    return {
        "passthrough_embed_title": endpoint_label or f"PolySniffer passthrough — ep{endpoint_id}",
        "passthrough_guard_head": mark_safe(guard),
        "passthrough_embed_head": mark_safe(head_static),
        "passthrough_embed_body": embed_body,
        "passthrough_browse_base": proxy_base,
        "passthrough_shell_base": shell_base,
        "passthrough_endpoint_id": endpoint_id,
        "passthrough_non_page_prefixes_json": json.dumps(list(np_prefixes)),
    }

```

## File 3 of 4: sniff_session.py

Repo path: `dose/polysniffer/sniff_session.py`

```python
"""PolySniffer 2.0 — capture session start/stop in the tenant schema."""
# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: PolySniffer 2.0 Native Login Workspace — 2026-06-24
from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from dose.polysniffer.har_capture import _ensure_tenant_schema
from dose.polysniffer.models import TrafficCapture
from dose.polysniffer.schema_patch import ensure_trafficlog_capture_columns
from dose.polysniffer.sniff_tenant import bind_request_tenant
from dose.utils import get_current_tenant


def _session_name(endpoint_id: int, mode: str) -> str:
    ts = timezone.now().strftime("%Y%m%d-%H%M")
    safe_mode = mode if mode in ("native", "passthrough") else "native"
    return f"ep{endpoint_id}-{safe_mode}-{ts}"


@staff_member_required
@require_http_methods(["POST"])
def session_start(request, endpoint_id: int):
    mode = (request.POST.get("mode") or "native").strip().lower()
    if mode not in ("native", "passthrough"):
        return JsonResponse({"error": "mode must be native or passthrough"}, status=400)

    tenant = bind_request_tenant(request) or get_current_tenant(request)
    if not tenant:
        return JsonResponse({"error": "no tenant context"}, status=400)

    ensure_trafficlog_capture_columns(request)
    _ensure_tenant_schema(tenant)

    TrafficCapture.objects.filter(tenant=tenant, is_active=True).update(is_active=False)
    cap = TrafficCapture.objects.create(
        tenant=tenant,
        capture_name=_session_name(endpoint_id, mode),
        description=f"PolySniffer 2.0 {mode} endpoint_id={endpoint_id}",
        is_active=True,
    )
    request.session[f"polysniffer_ep{endpoint_id}_mode"] = mode
    request.session[f"polysniffer_ep{endpoint_id}_capture_id"] = cap.id
    return JsonResponse(
        {
            "ok": True,
            "capture_id": cap.id,
            "capture_name": cap.capture_name,
            "mode": mode,
        }
    )


@staff_member_required
@require_http_methods(["POST"])
def session_stop(request, endpoint_id: int):
    tenant = bind_request_tenant(request) or get_current_tenant(request)
    if not tenant:
        return JsonResponse({"error": "no tenant context"}, status=400)

    _ensure_tenant_schema(tenant)
    updated = TrafficCapture.objects.filter(tenant=tenant, is_active=True).update(is_active=False)
    request.session.pop(f"polysniffer_ep{endpoint_id}_capture_id", None)
    request.session.pop(f"polysniffer_ep{endpoint_id}_mode", None)
    return JsonResponse({"ok": True, "stopped": updated})

```

## File 4 of 4: sniff_workspace.html

Repo path: `dose/templates/polysniffer/sniff_workspace.html`

```html
<!-- THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION -->
<!-- BINGO: PolySniffer 2.0 Native Login Workspace — 2026-06-24 -->
<!-- workspace shell: native-inline-v3 passthrough-inline-div -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>PolySniffer 2.0 — {% firstof endpoint_label "Workspace" %}</title>
    <style>
        * { box-sizing: border-box; }
        html, body { margin: 0; height: 100%; overflow: hidden; background: #111827; color: #e5e7eb; font-family: system-ui, sans-serif; }
        .topbar {
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 14px;
            background: #1f2937;
            border-bottom: 1px solid #374151;
            flex-shrink: 0;
        }
        .topbar h1 { margin: 0; font-size: 0.95rem; color: #34d399; }
        .topbar .meta { font-size: 0.8rem; color: #9ca3af; }
        .live { color: #6ee7b7; font-size: 0.78rem; }
        .split { display: grid; grid-template-columns: 1fr 420px; height: calc(100vh - 44px); }
        .left-col { display: flex; flex-direction: column; min-width: 0; border-right: 1px solid #374151; }
        .mode-picker {
            padding: 10px 12px;
            background: #0b1220;
            border-bottom: 1px solid #1f2937;
            flex-shrink: 0;
        }
        .mode-picker h2 { margin: 0 0 6px; font-size: 0.8rem; color: #9ca3af; font-weight: 600; }
        .mode-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px; }
        .mode-card {
            border: 1px solid #374151;
            border-radius: 8px;
            padding: 10px 12px;
            background: #1f2937;
        }
        .mode-card.selected { border-color: #34d399; box-shadow: 0 0 0 1px #34d399; }
        .mode-card.pt.selected { border-color: #60a5fa; box-shadow: 0 0 0 1px #60a5fa; }
        .mode-card h3 { margin: 0 0 4px; font-size: 0.85rem; }
        .mode-card p { margin: 0 0 8px; font-size: 0.72rem; color: #9ca3af; line-height: 1.4; }
        .btn {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 6px;
            border: none;
            font-size: 0.78rem;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            color: #fff;
        }
        .btn-native { background: #059669; }
        .btn-native:hover { background: #047857; }
        .btn-pt { background: #2563eb; }
        .btn-pt:hover { background: #1d4ed8; }
        .btn-secondary { background: #374151; color: #f3f4f6; }
        .btn-secondary:hover { background: #4b5563; }
        .toolbar { display: flex; gap: 6px; flex-wrap: wrap; }
        .proxy-wrap { flex: 1; display: flex; flex-direction: column; min-height: 0; }
        .proxy-wrap header { padding: 5px 10px; font-size: 0.72rem; color: #6b7280; background: #111827; border-bottom: 1px solid #1f2937; }
        #passthrough-inline {
            flex: 1;
            min-height: 0;
            overflow: auto;
            background: #fff;
            transform: translateZ(0);
            isolation: isolate;
        }
        #passthrough-inline .polysniffer-pt-scope {
            min-height: 100%;
            width: 100%;
        }
        .polysniffer-pt-orchestration-bar {
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        #native-inline {
            flex: 1;
            min-height: 0;
            overflow: auto;
            background: #fff;
        }
        #native-inline .polysniffer-native-scope {
            min-height: 100%;
            width: 100%;
        }
        .proxy-placeholder {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #1f2937;
            color: #6b7280;
            font-size: 0.9rem;
            text-align: center;
            padding: 24px;
            line-height: 1.6;
        }
        .right-col { display: flex; flex-direction: column; min-width: 0; min-height: 0; }
        .right-col header { padding: 6px 10px; font-size: 0.75rem; color: #4caf50; background: #1a1a1a; border-bottom: 2px solid #0f0; }
        #capture-frame { flex: 1; width: 100%; border: 0; background: #1a1a1a; }
        .error-box { margin: 40px auto; max-width: 520px; padding: 24px; background: #1f2937; border: 1px solid #7f1d1d; border-radius: 10px; color: #fecaca; }
        a { color: #93c5fd; }
    </style>
    {% if native_inline %}
    <base href="{{ native_inline.native_browse_base }}/">
    {{ native_inline.native_embed_head }}
    {% elif passthrough_inline %}
    {{ passthrough_inline.passthrough_guard_head }}
    <script>window.__PS_WORKSPACE_SHELL_PREFIX = '{{ passthrough_inline.passthrough_shell_base|escapejs }}';</script>
    {{ passthrough_inline.passthrough_embed_head }}
    {% endif %}
</head>
<body>
{% if error %}
<div class="error-box">
    <h2>PolySniffer unavailable</h2>
    <p>{{ error }}</p>
    <p><a href="/admin/dose/passthroughendpoint/">Back to endpoints</a></p>
</div>
{% else %}
<div class="topbar">
    <div>
        <h1>PolySniffer 2.0</h1>
        <span class="meta">{{ endpoint_label }}</span>
    </div>
    <div class="live" id="session-status">
        {% if active_session %}Recording · {{ active_session.capture_name }}{% else %}Pick a mode and start capture{% endif %}
    </div>
</div>

<div class="split">
    <section class="left-col">
        <div class="mode-picker">
            <h2>Parity triangle — native embed vs production passthrough</h2>
            <div class="mode-cards">
                <div class="mode-card{% if mode == 'native' %} selected{% endif %}" id="card-native">
                    <h3>Native</h3>
                    <p>Lightweight sniff embed — upstream content only, no orchestration bar.</p>
                    <a class="btn btn-native" href="/dose/sniff/{{ endpoint_id }}/workspace/native/">Start native</a>
                </div>
                <div class="mode-card pt{% if mode == 'passthrough' %} selected{% endif %}" id="card-passthrough">
                    <h3>Passthrough</h3>
                    <p>Full production chain — handlers, shim, orchestration bar, dynamic orchestration.</p>
                    <a class="btn btn-pt" href="/dose/sniff/{{ endpoint_id }}/workspace/passthrough/">Start passthrough</a>
                </div>
            </div>
            <div class="toolbar">
                <button type="button" class="btn btn-secondary" onclick="stopSession()">Stop capture</button>
                <a class="btn btn-secondary" href="{{ diff_url }}">Diff</a>
                <a class="btn btn-secondary" href="{{ export_url }}">Export HAR</a>
                <a class="btn btn-secondary" href="/admin/dose/passthroughendpoint/">Endpoints</a>
            </div>
        </div>
        <div class="proxy-wrap">
            <header id="browse-label">{% if native_inline %}Browse — native inline{{ browse_subpath }}{% elif passthrough_inline %}Browse — passthrough inline{{ browse_subpath }}{% elif mode == 'passthrough' and active_session %}Browse — passthrough (orchestration){% else %}Select a mode above{% endif %}</header>
            <div id="native-inline" class="native-inline"{% if not native_inline %} style="display:none"{% endif %}>
                {% if native_inline %}
                <div class="polysniffer-native-scope" data-polysniffer-workspace-embed="1">
                    {{ native_inline.native_embed_body }}
                </div>
                {% endif %}
            </div>
            <div id="passthrough-inline" class="passthrough-inline"{% if not passthrough_inline %} style="display:none"{% endif %}>
                {% if passthrough_inline %}
                {{ passthrough_inline.passthrough_embed_body }}
                {% endif %}
            </div>
            {% if native_inline_error %}
            <div class="proxy-placeholder" id="native-inline-error">{{ native_inline_error }}</div>
            {% endif %}
            {% if passthrough_inline_error %}
            <div class="proxy-placeholder" id="passthrough-inline-error">{{ passthrough_inline_error }}</div>
            {% endif %}
            <div class="proxy-placeholder" id="browse-placeholder"{% if active_session %} style="display:none"{% endif %}>
                Click <strong>Start native</strong> or <strong>Start passthrough</strong> above.<br>
                Native and passthrough both render inline in this panel; only capture uses an iframe.
            </div>
            {% if upstream_browse_url %}
            <div style="padding:6px 10px;font-size:0.72rem;background:#111827;border-top:1px solid #1f2937;">
                Browse blank or SSO stuck?
                <a id="browse-new-tab" href="{% if passthrough_inline %}{{ passthrough_inline.passthrough_browse_base }}{{ browse_subpath }}{% elif native_shell_url %}{{ native_shell_url }}{% else %}#{% endif %}" target="_blank" rel="noopener">Open in new tab</a> (last resort)
                &nbsp;|&nbsp;
                Baseline: <a href="{{ upstream_browse_url }}" target="_blank" rel="noopener">direct upstream{{ browse_subpath }}</a>
            </div>
            {% endif %}
        </div>
    </section>

    <section class="right-col">
        <header>Live capture</header>
        <iframe id="capture-frame" src="{{ capture_frame_url }}" title="PolySniffer live capture"></iframe>
    </section>
</div>

<script>
(function() {
    const csrf = '{{ csrf_token }}';
    const epId = {{ endpoint_id }};
    let currentMode = '{{ mode|escapejs }}';
    const browseSubpath = '{{ browse_subpath|escapejs }}';
    const captureFrameUrl = '{{ capture_frame_url }}';
    const hasNativeInline = {% if native_inline %}true{% else %}false{% endif %};
    const hasPassthroughInline = {% if passthrough_inline %}true{% else %}false{% endif %};
    const ptBrowsePrefix = {% if passthrough_inline %}'{{ passthrough_inline.passthrough_browse_base|escapejs }}'{% else %}''{% endif %};
    const ptBrowseUrl = {% if passthrough_inline %}'{{ passthrough_inline.passthrough_browse_base|escapejs }}{{ browse_subpath|escapejs }}'{% else %}''{% endif %};
    const nonPagePrefixes = {% if passthrough_inline %}{{ passthrough_inline.passthrough_non_page_prefixes_json|safe }}{% else %}[]{% endif %};

    function shellUrlForMode(mode) {
        return '/dose/sniff/' + epId + '/workspace/' + mode + '/';
    }

    function workspaceShellUrl() {
        var sub = browseSubpath || '';
        if (sub.charAt(0) === '/') sub = sub.slice(1);
        return '/dose/sniff/' + epId + '/workspace/' + sub;
    }

    function nativeShellUrl() {
        return shellUrlForMode('native');
    }

    function passthroughShellUrl() {
        return shellUrlForMode('passthrough');
    }

    function navigateToShell(url) {
        var sep = url.indexOf('?') >= 0 ? '&' : '?';
        window.location.replace(url + sep + '_=' + Date.now());
    }

    function browseLabel(mode) {
        if (mode === 'native') return 'Browse — native inline' + browseSubpath;
        if (mode === 'passthrough') return 'Browse — passthrough inline' + browseSubpath;
        return 'Select a mode above';
    }

    function refreshCaptureFrame(mode, force) {
        const cap = document.getElementById('capture-frame');
        if (!cap) return;
        const base = captureFrameUrl.split('?')[0];
        const wanted = mode ? base + '?mode=' + encodeURIComponent(mode) : base;
        if (force || cap.getAttribute('data-ps-mode') !== (mode || '')) {
            cap.setAttribute('data-ps-mode', mode || '');
            cap.src = wanted + (wanted.indexOf('?') >= 0 ? '&' : '?') + '_=' + Date.now();
        }
    }

    function setModeUI(mode, options) {
        options = options || {};
        currentMode = mode;
        document.getElementById('card-native').classList.toggle('selected', mode === 'native');
        document.getElementById('card-passthrough').classList.toggle('selected', mode === 'passthrough');
        document.getElementById('browse-label').textContent = browseLabel(mode);

        const placeholder = document.getElementById('browse-placeholder');
        const nativeInline = document.getElementById('native-inline');
        const ptInline = document.getElementById('passthrough-inline');
        const newTab = document.getElementById('browse-new-tab');

        if (mode === 'native') {
            if (placeholder) placeholder.style.display = 'none';
            if (ptInline) ptInline.style.display = 'none';
            if (nativeInline && hasNativeInline) {
                nativeInline.style.display = '';
            } else if (!options.skipNavigate) {
                navigateToShell(nativeShellUrl());
                return;
            }
            if (newTab) newTab.href = nativeShellUrl();
        } else if (mode === 'passthrough') {
            if (placeholder) placeholder.style.display = 'none';
            if (nativeInline) nativeInline.style.display = 'none';
            if (ptInline && hasPassthroughInline) {
                ptInline.style.display = '';
            } else if (!options.skipNavigate) {
                navigateToShell(passthroughShellUrl());
                return;
            }
            if (newTab) {
                newTab.href = ptBrowseUrl || passthroughShellUrl();
            }
        }

        refreshCaptureFrame(mode, !!options.forceCaptureReload);
    }

    window.startSession = async function(mode) {
        const fd = new FormData();
        fd.append('mode', mode);
        let r, j;
        try {
            r = await fetch('/dose/sniff/' + epId + '/session/start/', {
                method: 'POST',
                body: fd,
                credentials: 'same-origin',
                headers: {'X-CSRFToken': csrf}
            });
            j = await r.json();
        } catch (err) {
            alert('Failed to start capture: ' + (err && err.message ? err.message : err));
            return;
        }
        if (!j.ok) {
            alert(j.error || 'Failed to start capture');
            return;
        }
        document.getElementById('session-status').textContent = 'Recording · ' + j.capture_name;
        if (mode === 'native') {
            navigateToShell(nativeShellUrl());
            return;
        }
        if (mode === 'passthrough') {
            navigateToShell(passthroughShellUrl());
            return;
        }
        setModeUI(mode, { forceCaptureReload: true });
    };

    window.stopSession = async function() {
        let r, j;
        try {
            r = await fetch('/dose/sniff/' + epId + '/session/stop/', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {'X-CSRFToken': csrf}
            });
            j = await r.json();
        } catch (err) {
            alert('Failed to stop: ' + (err && err.message ? err.message : err));
            return;
        }
        if (!j.ok) {
            alert(j.error || 'Failed to stop');
            return;
        }
        currentMode = '';
        document.getElementById('session-status').textContent = 'Capture stopped — pick a mode above';
        var ph = document.getElementById('browse-placeholder');
        if (ph) ph.style.display = '';
        var ni = document.getElementById('native-inline');
        if (ni) ni.style.display = 'none';
        var pt = document.getElementById('passthrough-inline');
        if (pt) pt.style.display = 'none';
        document.getElementById('card-native').classList.remove('selected');
        document.getElementById('card-passthrough').classList.remove('selected');
        document.getElementById('browse-label').textContent = 'Select a mode above';
        refreshCaptureFrame('', true);
    };

    document.addEventListener('DOMContentLoaded', function() {
        if (hasPassthroughInline) {
            var ph = document.getElementById('browse-placeholder');
            if (ph) ph.style.display = 'none';
            var pt = document.getElementById('passthrough-inline');
            if (pt) pt.style.display = '';
        } else if (hasNativeInline) {
            var ph2 = document.getElementById('browse-placeholder');
            if (ph2) ph2.style.display = 'none';
            var ni = document.getElementById('native-inline');
            if (ni) ni.style.display = '';
        }
        const statusEl = document.getElementById('session-status');
        const isRecording = statusEl && statusEl.textContent.indexOf('Recording') >= 0;
        if (!currentMode && isRecording) {
            currentMode = captureFrameUrl.indexOf('mode=passthrough') >= 0 ? 'passthrough' : 'native';
        }
        if (currentMode && isRecording) {
            setModeUI(currentMode, {
                forceCaptureReload: true,
                skipNavigate: hasNativeInline || hasPassthroughInline
            });
            return;
        }
        if (!currentMode) return;
        if (isRecording) {
            setModeUI(currentMode, {
                forceCaptureReload: true,
                skipNavigate: hasNativeInline || hasPassthroughInline
            });
            return;
        }
        var path = window.location.pathname || '';
        if (/\/workspace\/(native|passthrough)\/?$/.test(path)) {
            startSession(currentMode);
        }
    });

    function isPassthroughAssetPath(path) {
        var low = (path || '').toLowerCase();
        if (!low || low.charAt(0) !== '/') low = '/' + (low || '');
        for (var i = 0; i < nonPagePrefixes.length; i++) {
            var p = nonPagePrefixes[i];
            if (p.charAt(0) !== '/') p = '/' + p;
            if (low.indexOf(p.toLowerCase()) === 0) return true;
        }
        var last = low.split('/').pop() || '';
        if (last.indexOf('.') > 0) {
            var ext = last.split('.').pop();
            if (/^(js|css|map|png|jpg|jpeg|gif|svg|ico|woff2?|json)$/.test(ext)) return true;
        }
        return false;
    }

    document.addEventListener('click', function(ev) {
        if (currentMode !== 'passthrough') return;
        if (!ptBrowsePrefix) return;
        var a = ev.target && ev.target.closest ? ev.target.closest('a[href]') : null;
        if (!a) return;
        if (a.id === 'browse-new-tab' || (a.getAttribute('target') || '').toLowerCase() === '_blank') return;
        try {
            var url = new URL(a.getAttribute('href'), window.location.origin);
            if (url.origin !== window.location.origin) return;
            if (url.pathname.indexOf(ptBrowsePrefix) !== 0) return;
            var sub = url.pathname.slice(ptBrowsePrefix.length);
            if (!sub || sub.charAt(0) !== '/') sub = '/' + (sub || '');
            if (isPassthroughAssetPath(sub)) return;
            ev.preventDefault();
            window.location.href = '/dose/sniff/' + epId + '/workspace' + sub + (url.search || '');
        } catch (e) {}
    }, true);
})();
</script>
{% if passthrough_inline %}
{% load static %}
<script src="{% static 'admin/js/orchestration_instruction_button.js' %}?v=20260611-8"></script>
<script>if (window.PolySaaSOrchBar) { PolySaaSOrchBar.initEmbed(); }</script>
{% endif %}
{% endif %}
</body>
</html>

```

