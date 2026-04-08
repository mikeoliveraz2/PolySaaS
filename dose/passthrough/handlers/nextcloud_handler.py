# dose/passthrough/handlers/nextcloud_handler.py
"""
Nextcloud passthrough handler — display-shell approach.

Strategy:
  - All HTML navigation (GET) goes through admin/display.html just like Odoo.
  - Static assets (.js .css .png etc.) bypass the shell and are forwarded directly.
  - API paths (/ocs/, /remote.php/, /heartbeat, /dav/, /avatar/, /preview) bypass.
  - A minimal fetch/XHR shim rewrites all same-origin Nextcloud paths through the proxy prefix.
  - Server-side URL rewriting rewrites href/src/action in the HTML body.
"""
import json
import logging
import re
from urllib.parse import urlparse

from django.http import HttpResponseRedirect

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths that must bypass the display shell and be forwarded as-is
# ---------------------------------------------------------------------------
_NC_BYPASS_PREFIXES = (
    "/ocs/",
    "/remote.php/",
    "/dav/",
    "/cron.php",
    "/status.php",
    "/ocm-provider",
    "/core/preview",
    "/index.php/heartbeat",
    "/index.php/avatar",
    "/index.php/core/preview",
    "/index.php/apps/files/ajax/",
    "/index.php/core/wopi/",
)

_NC_STATIC_EXTENSIONS = frozenset(
    "js css map woff woff2 ttf eot otf png jpg jpeg gif svg ico webp json wasm xml".split()
)


def _nc_bypasses_display_shell(upstream_subpath: str) -> bool:
    """Return True if this path should be forwarded directly (not wrapped in display shell)."""
    u = upstream_subpath or ""
    # Static file extensions
    last = u.rstrip("/").split("/")[-1]
    if "." in last:
        ext = last.rsplit(".", 1)[-1].lower()
        if ext in _NC_STATIC_EXTENSIONS:
            return True
    # Known API / binary paths
    for prefix in _NC_BYPASS_PREFIXES:
        if u == prefix.rstrip("/") or u.startswith(prefix):
            return True
    return False


class NextcloudPassthroughHandler:
    """
    Passthrough handler for Nextcloud.
    Implements try_root_display_shell_response so the middleware wraps HTML responses
    in admin/display.html (the same shell used for Odoo and Mattermost).
    """

    # ------------------------------------------------------------------
    # Display-shell entry point (called by middleware)
    # ------------------------------------------------------------------

    def try_root_display_shell_response(self, request, endpoint, url_trigger_segment):
        """
        Intercept GET requests and return display.html with Nextcloud head+body injected.
        Returns None for non-GET, static assets, and API calls so they fall through to
        the normal forward_request_standardized proxy path.
        """
        if request.method != "GET":
            return None

        seg = (
            url_trigger_segment.strip("/").lower().split("/")[-1].replace("-", "_")
        )
        proxy_prefix = f"/pt/admin/{seg}"
        path_info = request.path_info
        norm = path_info.rstrip("/")

        if norm == proxy_prefix:
            upstream_subpath = "/"
        elif path_info.startswith(proxy_prefix + "/"):
            upstream_subpath = path_info[len(proxy_prefix):]
            if not upstream_subpath.startswith("/"):
                upstream_subpath = "/" + upstream_subpath
        else:
            return None

        if _nc_bypasses_display_shell(upstream_subpath):
            return None

        from django.shortcuts import render

        display_head_inner = ""
        display_body_inner = ""

        if endpoint is not None:
            _parsed = urlparse(endpoint.endpoint_url)
            _base = f"{_parsed.scheme}://{_parsed.netloc}"

            fetch_path = upstream_subpath if upstream_subpath not in ("", "/") else "/"
            # Use our own fetch that handles Nextcloud's proxy-prefix redirects correctly.
            # fetch_upstream_index_html follows same-origin redirects by prepending the upstream
            # base, but Nextcloud may put /pt/admin/nextcloud/ in its Location headers (because
            # it was initialised with OVERWRITEWEBROOT), causing a redirect loop.
            raw_html = self._fetch_nc_html(_base, fetch_path, proxy_prefix, request)

            # If upstream redirected to a PolySaaS URL outside the proxy prefix → browser redirect
            redir = self._display_shell_redirect_from_fetch(raw_html, request, proxy_prefix)
            if redir is not None:
                return redir

            if raw_html and not raw_html.startswith("REDIRECT:"):
                # Extract <head> content
                m = re.search(r"<head[^>]*>(.*?)</head>", raw_html, re.DOTALL | re.IGNORECASE)
                if m:
                    head_raw = m.group(1).strip()
                    head_raw = self._strip_base_tags(head_raw)
                    head_raw = self._strip_csp_meta(head_raw)
                    display_head_inner = self._rewrite_nc_paths(head_raw, proxy_prefix, _base)

                # Extract <body> content
                m_body = re.search(r"<body[^>]*>(.*?)</body>", raw_html, re.DOTALL | re.IGNORECASE)
                if m_body:
                    body_raw = m_body.group(1).strip()
                    display_body_inner = self._rewrite_nc_paths(body_raw, proxy_prefix, _base)

            # Prepend early fetch/XHR shim so it runs before any Nextcloud inline scripts
            early_shim = self._build_early_shim(proxy_prefix, _base)
            display_head_inner = early_shim + display_head_inner

        return render(
            request,
            "admin/display.html",
            {
                "display_head_inner": display_head_inner,
                "display_body_inner": display_body_inner,
                "service_name": "Nextcloud",
                "proxy_prefix": proxy_prefix,
            },
        )

    @staticmethod
    def _fetch_nc_html(base: str, path: str, proxy_prefix: str, request) -> str:
        """
        Fetch HTML from Nextcloud upstream.

        KEY INSIGHT: When fetching via 'localhost', Nextcloud matches its OVERWRITEHOST
        setting and issues redirect loops back to the PolySaaS host. Fetching via
        '127.0.0.1' bypasses OVERWRITEHOST matching and returns HTML directly.
        We normalise 'localhost' → '127.0.0.1' before making any request.
        """
        import requests as _rq

        # Force IP address so Nextcloud's OVERWRITEHOST rule doesn't match.
        fetch_base = base.replace("localhost", "127.0.0.1")

        # Do NOT pass browser cookies — old nc_session cookies in the browser (from
        # direct localhost:8888 access) cause Nextcloud to redirect away from /login
        # instead of serving the page HTML, creating a redirect loop.  The display-shell
        # fetch only needs the page structure; auth is handled by the login POST.
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; PolySaaS-Proxy/1.0)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }

        current_path = path
        for hop in range(6):
            url = fetch_base.rstrip("/") + current_path
            print(f"[NC_FETCH] Hop {hop}: GET {url}")
            try:
                resp = _rq.get(url, headers=headers, cookies={},
                               allow_redirects=False, timeout=30)
            except Exception as exc:
                print(f"[NC_FETCH] Request failed: {exc}")
                return ""

            print(f"[NC_FETCH] Hop {hop}: Status {resp.status_code}")

            if resp.status_code == 200:
                ct = resp.headers.get("Content-Type", "")
                if "text/html" in ct:
                    print(f"[NC_FETCH] Got HTML ({len(resp.content)} bytes)")
                    return resp.text
                print(f"[NC_FETCH] Non-HTML content-type: {ct}")
                return ""

            if resp.status_code in (301, 302, 303, 307, 308):
                loc = resp.headers.get("Location", "")
                if not loc:
                    break
                print(f"[NC_FETCH] Redirect to: {loc}")

                # Make relative paths absolute (they're relative to upstream origin, not proxy)
                if loc.startswith("/"):
                    # Strip proxy prefix if Nextcloud injected it
                    if loc.startswith(proxy_prefix):
                        loc = loc[len(proxy_prefix):]
                        if not loc.startswith("/"):
                            loc = "/" + loc
                    # Strip double-appended proxy prefix loops
                    while "/nextcloud/index.phpnextcloud" in loc or \
                          "index.phpnextcloud" in loc:
                        loc = loc.split("index.phpnextcloud")[0] + "index.php"
                    current_path = loc
                    continue

                # Absolute URL — cross-origin means Nextcloud wants browser to go there
                loc_parsed = urlparse(loc)
                loc_origin = f"{loc_parsed.scheme}://{loc_parsed.netloc}"
                if loc_origin != fetch_base:
                    # Return as sentinel so caller can decide what to do
                    return f"REDIRECT:{resp.status_code}:{loc}"
                # Same-origin absolute: extract path
                current_path = loc_parsed.path
                if loc_parsed.query:
                    current_path += "?" + loc_parsed.query
                continue

            # Any other status
            print(f"[NC_FETCH] Unexpected status {resp.status_code}")
            return ""

        print("[NC_FETCH] Exceeded hop limit")
        return ""

    @staticmethod
    def _display_shell_redirect_from_fetch(raw_html, request, proxy_prefix):
        """
        fetch_upstream_index_html returns REDIRECT:status:url when Location is not the same
        origin as the upstream base (e.g. Nextcloud -> http://localhost:8000/pt/admin/nextcloud/login).
        Tell the browser to follow that URL so the display shell loads on the next GET.
        """
        if not raw_html or not raw_html.startswith("REDIRECT:"):
            return None
        parts = raw_html.split(":", 2)
        if len(parts) < 3:
            return None
        location = parts[2].strip()
        if not location:
            return None
        loc_parsed = urlparse(location)
        path = loc_parsed.path or ""
        if not path.startswith(proxy_prefix):
            return None
        target = path
        if loc_parsed.query:
            target = f"{path}?{loc_parsed.query}"
        return HttpResponseRedirect(target)

    # ------------------------------------------------------------------
    # URL resolution (called by forwarding.py)
    # ------------------------------------------------------------------

    def upstream_url_for_subpath(self, endpoint_url, clean_path):
        """Map a proxied subpath to the real Nextcloud URL."""
        parsed = urlparse(endpoint_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if clean_path in ("/", ""):
            return endpoint_url.rstrip("/") + "/"
        return base.rstrip("/") + clean_path

    # ------------------------------------------------------------------
    # HTML processing (called by forwarding.py for non-shell responses)
    # ------------------------------------------------------------------

    def process_html_response(self, html_str, response, endpoint_url=None, *args, **kwargs):
        """Rewrite URLs in proxied HTML that bypasses the display shell."""
        if not endpoint_url:
            return html_str, None
        parsed = urlparse(endpoint_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        proxy_prefix = "/pt/admin/nextcloud"
        html_str = self._rewrite_nc_paths(html_str, proxy_prefix, base)
        return html_str, None

    # ------------------------------------------------------------------
    # Server-side URL rewriting
    # ------------------------------------------------------------------

    def _rewrite_nc_paths(self, html: str, proxy_prefix: str, base: str) -> str:
        """
        Rewrite absolute Nextcloud paths in HTML attributes to go through the proxy prefix.
        Covers href, src, action, data-url, data-href, and JSON strings in <script> blocks.
        """
        # Patterns that should be proxied (navigation + APIs)
        _NC_PROXY_PREFIXES = (
            "/index.php/",
            "/core/",
            "/apps/",
            "/ocs/",
            "/remote.php/",
            "/heartbeat",
            "/avatar/",
        )

        def rewrite_attr_value(match):
            attr = match.group(1)
            quote = match.group(2)
            url = match.group(3)
            if not url:
                return match.group(0)
            if url.startswith("data:") or url.startswith("javascript:") or url.startswith("#"):
                return match.group(0)
            # Absolute upstream URL → proxy
            if url.startswith(base + "/"):
                return f'{attr}={quote}{proxy_prefix}{url[len(base):]}{quote}'
            # Relative root paths for NC
            if url.startswith("/") and not url.startswith(proxy_prefix):
                for pfx in _NC_PROXY_PREFIXES:
                    if url.startswith(pfx) or url == pfx.rstrip("/"):
                        return f'{attr}={quote}{proxy_prefix}{url}{quote}'
            return match.group(0)

        # Rewrite in standard HTML attributes
        attr_pattern = r'((?:href|src|action|data-url|data-href|data-link))=([\"\'])(/[^\"\'#\s]*?)\2'
        html = re.sub(attr_pattern, rewrite_attr_value, html, flags=re.IGNORECASE)

        # Rewrite absolute base URLs embedded in JS strings / JSON (e.g. OC.webroot, baseUrl)
        html = html.replace(f'"{base}/', f'"{proxy_prefix}/')
        html = html.replace(f"'{base}/", f"'{proxy_prefix}/")

        return html

    # ------------------------------------------------------------------
    # Helper strippers
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_base_tags(html: str) -> str:
        return re.sub(r"<base[^>]*/?>", "", html, flags=re.IGNORECASE)

    @staticmethod
    def _strip_csp_meta(html: str) -> str:
        return re.sub(
            r'<meta[^>]+http-equiv=["\']Content-Security-Policy["\'][^>]*/?>',
            "",
            html,
            flags=re.IGNORECASE,
        )

    # ------------------------------------------------------------------
    # Early fetch/XHR shim (injected into <head> before Nextcloud scripts)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_early_shim(proxy_prefix: str, base: str) -> str:
        """
        Minimal JS shim injected before Nextcloud's inline scripts.
        Patches fetch, XHR, and navigation so same-origin Nextcloud calls route through proxy.
        Also patches OC.generateUrl / OC.filePath.
        """
        nc_paths_js = json.dumps([
            "/index.php/", "/core/", "/apps/", "/ocs/", "/remote.php/",
            "/heartbeat", "/avatar/", "/csrftoken", "/cron.php",
        ])
        return f"""<script data-polysaas-nc-shim="1">
(function(){{
'use strict';
var PROXY={json.dumps(proxy_prefix)};
var BASE={json.dumps(base)};
var NC_PATHS={nc_paths_js};

function _toProxy(u){{
    if(!u||typeof u!=='string')return u;
    // Absolute upstream URL
    if(u.indexOf(BASE)===0)return PROXY+u.slice(BASE.length);
    // Already proxied
    if(u.startsWith(PROXY))return u;
    if(u.charAt(0)==='/'){{
        for(var i=0;i<NC_PATHS.length;i++){{
            if(u.startsWith(NC_PATHS[i])||u===NC_PATHS[i].replace(/\\/$/,'')){{
                return PROXY+u;
            }}
        }}
    }}
    return u;
}}

// Patch fetch
var _f=window.fetch;
window.fetch=function(input,init){{
    if(typeof input==='string')input=_toProxy(input);
    else if(typeof Request!=='undefined'&&input instanceof Request){{
        var n=_toProxy(input.url);if(n!==input.url)input=new Request(n,input);
    }}
    return _f.call(this,input,init);
}};

// Patch XHR
var _x=XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open=function(){{
    var a=Array.prototype.slice.call(arguments);
    a[1]=_toProxy(a[1]);
    return _x.apply(this,a);
}};

// Patch OC.generateUrl (Nextcloud's URL builder)
function _patchOC(){{
    if(!window.OC)return;
    if(window.OC.generateUrl&&!window.OC.generateUrl._ncPatched){{
        var orig=window.OC.generateUrl;
        window.OC.generateUrl=function(url,params,opts){{
            var r=orig.call(this,url,params,opts);
            return _toProxy(r);
        }};
        window.OC.generateUrl._ncPatched=true;
    }}
    if(window.OC.filePath&&!window.OC.filePath._ncPatched){{
        var origFP=window.OC.filePath;
        window.OC.filePath=function(app,type,file){{
            var r=origFP.call(this,app,type,file);
            return _toProxy(r);
        }};
        window.OC.filePath._ncPatched=true;
    }}
    if(window.OC.webroot!==undefined&&window.OC.webroot===''&&!window._ncWebrootPatched){{
        window._ncWebrootPatched=true;
        try{{Object.defineProperty(window.OC,'webroot',{{get:function(){{return PROXY;}},configurable:true}});}}catch(e){{}}
    }}
}}

// Patch navigation redirect so Nextcloud doesn't escape the proxy
var _pushState=history.pushState;
history.pushState=function(state,title,url){{
    if(url)url=_toProxy(url);
    return _pushState.call(this,state,title,url);
}};
var _replaceState=history.replaceState;
history.replaceState=function(state,title,url){{
    if(url)url=_toProxy(url);
    return _replaceState.call(this,state,title,url);
}};

// Run OC patch now and again after scripts load
_patchOC();
[100,300,600,1200,2500].forEach(function(ms){{setTimeout(_patchOC,ms);}});

console.log('[PolySaaS] Nextcloud shim active, proxy='+PROXY);
}})();
</script>
"""

    # ------------------------------------------------------------------
    # Static asset handling stub (used by some middleware paths)
    # ------------------------------------------------------------------

    def handle_static_asset(self, request_path, ext_path_str):
        return None
