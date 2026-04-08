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
        from dose.passthrough.forwarding import fetch_upstream_index_html

        display_head_inner = ""
        display_body_inner = ""

        if endpoint is not None:
            _parsed = urlparse(endpoint.endpoint_url)
            _base = f"{_parsed.scheme}://{_parsed.netloc}"

            fetch_path = upstream_subpath if upstream_subpath not in ("", "/") else "/"
            raw_html = fetch_upstream_index_html(
                request,
                endpoint.endpoint_url,
                fetch_path,
                handler=self,
            )

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
