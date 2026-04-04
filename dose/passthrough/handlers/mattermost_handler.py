# dose/passthrough/handlers/mattermost_handler.py
"""
Mattermost SPA passthrough handler.

Only the initial HTML page load flows through the proxy (/pt/admin/mattermost/).
ALL subsequent traffic (static assets, API calls, WebSocket) goes DIRECT to the
upstream Mattermost origin. The shim injects the auth token client-side so the
browser can authenticate directly with Mattermost.
"""

import json
import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class MattermostPassthroughHandler:

    def process_html_response(self, html_str, request, endpoint_url=None, *args, **kwargs):
        logger.info("[MATTERMOST HANDLER] Processing HTML shell")

        if not endpoint_url:
            return html_str, None

        origin = endpoint_url.rstrip("/")
        parsed = urlparse(origin)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"

        site_path_prefix = self._site_path_prefix(endpoint_url)
        mm_token = self._get_mm_token(request)

        html_str = self._rewrite_asset_tags(html_str, base_origin, site_path_prefix)
        html_str = self._strip_base_tags(html_str)
        html_str = self._strip_meta_redirects(html_str)
        html_str = self._strip_csp(html_str)
        html_str = self._inject_client_shim(
            html_str, base_origin, site_path_prefix, mm_token
        )

        return html_str, None

    def _get_mm_token(self, request):
        """Retrieve the provisioned Mattermost token for the current tenant."""
        try:
            from dose.models import TenantApp
            from dose.utils import get_current_tenant
            tenant = get_current_tenant(request)
            if not tenant:
                return None
            ta = TenantApp.objects.filter(
                tenant=tenant, app_name='mattermost', status='active',
            ).first()
            if ta and ta.extra_config:
                return ta.extra_config.get('mm_token')
        except Exception as exc:
            logger.warning("[MATTERMOST HANDLER] Could not load mm_token: %s", exc)
        return None

    def build_admin_embed_injection(self, html_str, request, endpoint_url=None):
        """
        Fragments for admin/passthrough_embed.html: upstream banner + head styles only.
        Injected into the existing Jazzmin layout (not a separate document).
        """
        if not endpoint_url or not html_str:
            return {"head": "", "body": ""}
        origin = endpoint_url.rstrip("/")
        parsed = urlparse(origin)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"
        site_path_prefix = self._site_path_prefix(endpoint_url)

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_str, "html.parser")
        banner = (
            soup.find("header")
            or soup.find(attrs={"role": "banner"})
            or soup.find(id=re.compile(r"global.*header|navbar|topbar", re.I))
            or soup.select_one("[class*='global-header']")
        )

        head_chunks = []
        head = soup.head
        if head:
            for link in head.find_all("link", href=True):
                rel = link.get("rel")
                rel_list = rel if isinstance(rel, (list, tuple)) else ([rel] if rel else [])
                if "stylesheet" in rel_list:
                    head_chunks.append(str(link))
            for st in head.find_all("style"):
                head_chunks.append(str(st))
            for meta in head.find_all("meta"):
                if meta.get("name") == "viewport" or meta.get("charset"):
                    head_chunks.append(str(meta))

        head_html = "\n".join(head_chunks)
        head_html = self._rewrite_asset_tags(head_html, base_origin, site_path_prefix)

        if not banner:
            body = (
                '<div class="alert alert-info" style="margin-bottom:12px;">'
                "No static &lt;header&gt; in this HTML yet — Mattermost usually mounts the top bar "
                "in React. Styles from the shell are still injected; full app below.</div>"
            )
        else:
            body = self._rewrite_asset_tags(str(banner), base_origin, site_path_prefix)

        print(
            f"[MATTERMOST HANDLER] build_admin_embed_injection banner_found={bool(banner)} "
            f"head_len={len(head_html)} body_len={len(body)}"
        )
        return {"head": head_html, "body": body}

    def _passthrough_prefix(self, request):
        path = getattr(request, "path_info", "") or ""
        m = re.match(r"^(/pt/(?:admin|dose)/[^/]+)", path)
        if m:
            return m.group(1).rstrip("/")
        return "/pt/admin/mattermost"

    def _site_path_prefix(self, endpoint_url):
        """e.g. https://host/mattermost -> '/mattermost'; root install -> ''."""
        if not endpoint_url:
            return ""
        path = (urlparse(endpoint_url.rstrip("/")).path or "").rstrip("/")
        return path if path and path != "/" else ""

    def _path_tail_after_site_prefix(self, path: str, site_prefix: str) -> str:
        """'/mattermost/api/v1' + site '/mattermost' -> '/api/v1'; site root -> '/'."""
        sp = (site_prefix or "").rstrip("/")
        p = path or "/"
        if not p.startswith("/"):
            p = "/" + p
        if not sp:
            return p
        pl = p.rstrip("/")
        sl = sp.rstrip("/")
        if pl == sl:
            return "/"
        if pl == "":
            return "/"
        if p.startswith(sp + "/"):
            rest = p[len(sp) :]
            return rest if rest.startswith("/") else "/" + rest
        return p

    def _strip_base_tags(self, html: str) -> str:
        """
        Mattermost ships <base href="…/mattermost/">. In the Jazzmin embed that tag lives in our
        document <head> and repoints the entire admin UI + breaks the SPA. Remove all <base> tags.
        """
        if not html:
            return html
        return re.sub(r"<base\b[^>]*>", "", html, flags=re.IGNORECASE)

    def _strip_meta_redirects(self, html: str) -> str:
        """Remove <meta http-equiv="refresh"> tags that would navigate the embed away."""
        if not html:
            return html
        return re.sub(
            r'<meta\s+http-equiv\s*=\s*["\']refresh["\'][^>]*>',
            "", html, flags=re.IGNORECASE,
        )

    def _strip_csp(self, html: str) -> str:
        """Remove Content-Security-Policy meta tags — the proxy serves cross-origin assets."""
        if not html:
            return html
        return re.sub(
            r'<meta\s+http-equiv\s*=\s*["\']Content-Security-Policy["\'][^>]*>',
            "", html, flags=re.IGNORECASE,
        )

    def _rewrite_asset_tags(self, html, base_origin, site_path_prefix=""):
        """Rewrite root-relative URLs in HTML to point directly to the upstream origin."""

        pref = (site_path_prefix or "").rstrip("/")
        upstream = base_origin.rstrip("/")

        def rewrite_attr(match):
            attr = match.group(1)
            quote = match.group(2)
            url = match.group(3)
            if not url or url.startswith(("data:", "javascript:", "#", "mailto:")):
                return match.group(0)
            if url.startswith(("http://", "https://", "//")):
                return match.group(0)
            if not url.startswith("/"):
                return match.group(0)
            tail = self._path_tail_after_site_prefix(url, pref) if pref else url
            return f"{attr}={quote}{upstream}{tail}{quote}"

        pattern = r'(src|href)=([\"\'])(/[^\"\']*?)\2'
        return re.sub(pattern, rewrite_attr, html)

    def _inject_client_shim(self, html, base_origin, site_path_prefix="", mm_token=None):
        base_json = json.dumps(base_origin)
        mm_json = json.dumps((site_path_prefix or "").rstrip("/"))
        token_json = json.dumps(mm_token or "")
        patch = f"""
<script data-polysaas-mattermost-shim="1">
(function() {{
var B = {base_json};
var M = {mm_json};
var T = {token_json};
var O = window.location.origin;
var REAL_EMBED_PATH = window.location.pathname;
// Tell MM's router we're at "/" so it recognises the route
try {{ history.replaceState(null, '', '/'); }} catch(e) {{}}
function stripMmSubpath(s) {{
  if (!M) return s;
  if (s === M || s.startsWith(M + '/')) return (s === M) ? '/' : s.slice(M.length);
  return s;
}}
// Rewrite root-relative URLs to point at the upstream Mattermost origin
function toUpstream(s) {{
  if (typeof s !== 'string') return s;
  if (!s || s.startsWith('data:') || s.startsWith('blob:')) return s;
  if (s.startsWith(B)) return s;
  if (s.startsWith('http:') || s.startsWith('https:') || s.indexOf('//') === 0) {{
    if (s.startsWith(O + '/')) s = s.slice(O.length);
    else if (s === O) s = '/';
    else return s;
  }}
  if (s.charAt(0) !== '/') return s;
  s = stripMmSubpath(s);
  if (s.charAt(0) !== '/') return s;
  return B + s;
}}
// Inject auth token on API calls to Mattermost
function addAuth(url, init) {{
  if (!T) return init;
  try {{
    var u = new URL(url, location.href);
    var b = new URL(B);
    if (u.host === b.host && u.pathname.indexOf('/api/') !== -1) {{
      init = init || {{}};
      var h = init.headers ? new Headers(init.headers) : new Headers();
      if (!h.has('Authorization')) h.set('Authorization', 'Bearer ' + T);
      init.headers = h;
    }}
  }} catch(e) {{}}
  return init;
}}
var _f = window.fetch;
window.fetch = function(input, init) {{
  if (typeof input === 'string') {{
    input = toUpstream(input);
    init = addAuth(input, init);
  }} else if (typeof Request !== 'undefined' && input instanceof Request) {{
    var u = toUpstream(input.url);
    if (u !== input.url) input = new Request(u, input);
    init = addAuth(u, init);
  }}
  return _f.call(this, input, init);
}};
var _xo = XMLHttpRequest.prototype.open;
var _xSetHeader = XMLHttpRequest.prototype.setRequestHeader;
XMLHttpRequest.prototype.open = function(method, url) {{
  this._psUrl = toUpstream(url);
  var rest = Array.prototype.slice.call(arguments, 2);
  return _xo.apply(this, [method, this._psUrl].concat(rest));
}};
var _xSend = XMLHttpRequest.prototype.send;
XMLHttpRequest.prototype.send = function(body) {{
  if (T && this._psUrl) {{
    try {{
      var u = new URL(this._psUrl, location.href);
      var b = new URL(B);
      if (u.host === b.host && u.pathname.indexOf('/api/') !== -1) {{
        try {{ _xSetHeader.call(this, 'Authorization', 'Bearer ' + T); }} catch(e) {{}}
      }}
    }} catch(e) {{}}
  }}
  return _xSend.call(this, body);
}};
// WebSocket direct to Mattermost
var _WS = WebSocket;
window.WebSocket = function(url, protocols) {{
  if (typeof url === 'string') {{
    var wsUrl = toUpstream(url);
    try {{
      var u = new URL(wsUrl);
      u.protocol = u.protocol === 'https:' ? 'wss:' : 'ws:';
      if (T) u.searchParams.set('access_token', T);
      wsUrl = u.toString();
    }} catch(e) {{
      wsUrl = wsUrl.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:');
    }}
    url = wsUrl;
  }}
  return protocols === undefined ? new _WS(url) : new _WS(url, protocols);
}};
// Webpack chunk loading — point at upstream
function patchProp(proto, prop) {{
  var d = Object.getOwnPropertyDescriptor(proto, prop);
  if (!d || !d.set) return;
  Object.defineProperty(proto, prop, {{
    get: d.get,
    set: function(v) {{ d.set.call(this, toUpstream(v)); }},
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
      value = toUpstream(value);
    }}
  }}
  return _setAttr.call(this, name, value);
}};
// === Navigation lock ===
var _pushState = history.pushState;
var _replaceState = history.replaceState;
history.pushState = function(state, title, url) {{
  return _pushState.call(this, state, title, '/');
}};
history.replaceState = function(state, title, url) {{
  return _replaceState.call(this, state, title, '/');
}};
window.addEventListener('beforeunload', function() {{
  try {{ _replaceState.call(history, null, '', REAL_EMBED_PATH); }} catch(e) {{}}
}});
var _locReplace = Location.prototype.replace;
Location.prototype.replace = function(url) {{
  if (typeof url === 'string' && (url.charAt(0) === '/' || url.startsWith(O)) && !url.startsWith(B)) {{
    console.log('[PolySaaS] blocked location.replace:', url);
    return;
  }}
  return _locReplace.call(this, url);
}};
var _locAssign = Location.prototype.assign;
Location.prototype.assign = function(url) {{
  if (typeof url === 'string' && (url.charAt(0) === '/' || url.startsWith(O)) && !url.startsWith(B)) {{
    console.log('[PolySaaS] blocked location.assign:', url);
    return;
  }}
  return _locAssign.call(this, url);
}};
try {{
  var hrefDesc = Object.getOwnPropertyDescriptor(Location.prototype, 'href');
  if (hrefDesc && hrefDesc.set) {{
    Object.defineProperty(Location.prototype, 'href', {{
      get: hrefDesc.get,
      set: function(v) {{
        if (typeof v === 'string' && (v.charAt(0) === '/' || v.startsWith(O)) && !v.startsWith(B)) {{
          console.log('[PolySaaS] blocked location.href =', v);
          return;
        }}
        hrefDesc.set.call(this, v);
      }},
      configurable: true,
      enumerable: true
    }});
  }}
}} catch(e) {{ console.warn('[PolySaaS] could not override location.href:', e); }}
}})();
</script>
"""
        lower = html.lower()
        idx = lower.find("<head>")
        if idx != -1:
            ins = idx + len("<head>")
            return html[:ins] + patch + html[ins:]
        if "</head>" in html:
            return html.replace("</head>", patch + "</head>", 1)
        return patch + html

    def rewrite_upstream_body(self, body, content_type, request, **kwargs):
        """No-op: API calls go direct to Mattermost, not through the proxy."""
        return None
