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
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Odoo display-shell fetch/XHR/SW runtime lives in templates/admin/display.html extrajs
# (end of body) so it runs after Jazzmin sync scripts and before deferred Odoo modules.

def _odoo_upstream_bypasses_display_shell(upstream_subpath: str) -> bool:
    """
    If True, try_root_display_shell_response returns None so the request is
    forwarded to Odoo (JSON/binary/assets). Never use startswith('/web') alone —
    it would false-match /website, /websocket, etc.
    """
    u = upstream_subpath or ""
    # /web exact = Odoo app home after login redirect — must go through display shell, not be bypassed.
    # /web/ subdpaths (assets, datasets, actions, binary, session) are API/asset calls → bypass.
    if u.startswith("/web/"):
        return True
    if u == "/website" or u.startswith("/website/"):
        return True
    if u == "/bus" or u.startswith("/bus/"):
        return True
    if u == "/jsonrpc" or u.startswith("/jsonrpc/"):
        return True
    if u.startswith("/json/"):
        return True
    if u == "/longpolling" or u.startswith("/longpolling/"):
        return True
    if u == "/websocket" or u.startswith("/websocket/"):
        return True
    if u == "/mail" or u.startswith("/mail/"):
        return True
    return False


class OdooPassthroughHandler:

    def native_passthrough_prefixes(self):
        return ("/web", "/odoo", "/bus", "/websocket", "/longpolling")

    def should_follow_upstream_redirects(self, request, target_url: str, upstream_path: str) -> bool:
        """Odoo often redirects internally before landing on the usable page/document."""
        return True

    def augment_outbound_headers(self, request, headers: dict, target_url: str) -> None:
        """
        Every Odoo upstream call (including display-shell HTML fetch) must see proxy headers
        so generated asset URLs and web.base.url logic match the browser-facing PolySaaS host.
        """
        if not target_url:
            return
        parsed = urlparse(target_url)
        if not parsed.netloc:
            return
        headers["Host"] = parsed.netloc
        headers["X-Forwarded-For"] = request.META.get("REMOTE_ADDR", "")
        headers["X-Forwarded-Proto"] = "https" if request.is_secure() else "http"
        headers["X-Forwarded-Host"] = request.get_host()
        try:
            headers["X-Forwarded-Port"] = str(request.get_port())
        except Exception:
            headers["X-Forwarded-Port"] = "443" if request.is_secure() else "80"
        headers.pop("Referer", None)

    def upstream_url_for_subpath(self, endpoint_url, clean_path):
        """
        Initial HTML (path /): use the full configured endpoint_url (e.g. .../web/login).
        All other upstream paths: only scheme://netloc + path so assets and RPC never stack
        onto the login (or other entry) path from endpoint_url.
        """
        if not endpoint_url:
            return None
        parsed = urlparse(endpoint_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if clean_path in ("/", ""):
            return endpoint_url.rstrip("/") + "/"
        return base.rstrip("/") + clean_path

    def try_root_display_shell_response(self, request, endpoint, url_trigger_segment):
        """
        GET under /pt/admin/<trigger>/: same display.html shell as root; not only exact root.
        Upstream path = suffix after /pt/admin/<seg> (or / for root). Head always from HTML;
        body inner only for non-root paths (root stays empty so the SPA owns #wrapwrap — avoids
        double DOM vs server snapshot). quoted /web/ rewrite + XHR patch. Static ext → forward.
        """
        if request.method != "GET":
            return None
        # Skip display shell for remote hostname triggers (e.g. polysaas-odoo2.onrender.com).
        # The server-side pre-fetch fails for remote hosts; forward_request_standardized
        # is the correct path — it proxies the real browser request with its cookies.
        seg = url_trigger_segment.strip("/")
        if "." in seg:
            return None
        proxy_prefix = f"/pt/admin/{seg}"
        path_info = request.path_info
        norm = path_info.rstrip("/")
        if norm == proxy_prefix:
            upstream_subpath = "/"
        elif path_info.startswith(proxy_prefix + "/"):
            upstream_subpath = path_info[len(proxy_prefix) :]
            if not upstream_subpath.startswith("/"):
                upstream_subpath = "/" + upstream_subpath
        else:
            return None

        # Before any display-shell work: API, bus, jsonrpc, /web/*, /website/* (translations, etc.).
        if _odoo_upstream_bypasses_display_shell(upstream_subpath):
            return None

        last_seg = path_info.rstrip("/").split("/")[-1]
        if "." in last_seg:
            ext = last_seg.rsplit(".", 1)[-1].lower()
            if ext in (
                "js",
                "css",
                "map",
                "png",
                "jpg",
                "jpeg",
                "gif",
                "svg",
                "ico",
                "woff",
                "woff2",
                "ttf",
                "eot",
                "webp",
                "json",
                "wasm",
            ):
                return None

        from django.shortcuts import render
        from django.utils.safestring import mark_safe

        from dose.passthrough.forwarding import fetch_upstream_index_html

        display_head_inner = ""
        display_body_inner = ""

        if endpoint is not None:
            parsed_endpoint = urlparse(endpoint.endpoint_url)
            upstream_origin = f"{parsed_endpoint.scheme}://{parsed_endpoint.netloc}"
            # Display shell root only: fetch /web on upstream base; path "/" unchanged for body logic.
            fetch_path = (
                "/web"
                if upstream_subpath.rstrip("/") in ("", "/")
                else upstream_subpath
            )
            fetch_dbg = {}
            raw_html = fetch_upstream_index_html(
                request,
                endpoint.endpoint_url,
                fetch_path,
                handler=self,
                fetch_debug=fetch_dbg,
            )
            # Windows / mixed stacks: localhost sometimes fails where 127.0.0.1 works for requests.
            if (
                not raw_html
                and endpoint.endpoint_url
                and "localhost" in endpoint.endpoint_url
                and "127.0.0.1" not in endpoint.endpoint_url
            ):
                alt_ep = endpoint.endpoint_url.replace("localhost", "127.0.0.1", 1)
                if alt_ep != endpoint.endpoint_url:
                    fetch_dbg["retried_as"] = alt_ep
                    raw_html = fetch_upstream_index_html(
                        request,
                        alt_ep,
                        fetch_path,
                        handler=self,
                        fetch_debug=fetch_dbg,
                    )
            if raw_html and not raw_html.startswith("REDIRECT:"):
                logger.info(f"[ODOO HANDLER] Processing HTML ({len(raw_html)} chars)")
                m = re.search(
                    r"<head[^>]*>(.*?)</head>",
                    raw_html,
                    re.DOTALL | re.IGNORECASE,
                )
                if m:
                    head_raw = m.group(1).strip()
                    display_head_inner = self._strip_base_tags(head_raw)
                    logger.info(f"[ODOO HANDLER] Extracted head ({len(display_head_inner)} chars)")
                else:
                    logger.warning("[ODOO HANDLER] No <head> tag found in HTML")
                # TEMP DEBUG (CC): always extract upstream <body> so display.html <pre> shows raw HTML.
                # Revert: wrap below in `if upstream_subpath.rstrip("/") not in ("", "/"):` — root was
                # body-empty so SPA mounts #wrapwrap client-side; full body here can break layout.
                m_body = re.search(
                    r"<body[^>]*>(.*?)</body>",
                    raw_html,
                    re.DOTALL | re.IGNORECASE,
                )
                if m_body:
                    display_body_inner = m_body.group(1).strip()
                    logger.info(f"[ODOO HANDLER] Extracted body ({len(display_body_inner)} chars)")
                else:
                    # Fallback: no body tag found - wrap entire HTML for display
                    logger.warning("[ODOO HANDLER] No <body> tag found, using raw HTML fallback")
                    display_body_inner = f'<div class="odoo-raw-content">{raw_html}</div>'
            elif raw_html and raw_html.startswith("REDIRECT:"):
                from django.utils.html import escape as _esc

                loc = _esc(str(fetch_dbg.get("location") or ""))
                display_body_inner = (
                    '<div class="alert alert-warning" style="margin:16px;">'
                    'Odoo display shell received an upstream redirect instead of HTML. '
                    'The proxy shell rendered, but the upstream app did not provide boot HTML.'
                    + (f"<br><small>Location: {loc}</small>" if loc else "")
                    + "</div>"
                )
            else:
                from django.utils.html import escape as _esc

                detail_parts = []
                if fetch_dbg.get("error"):
                    detail_parts.append(f"Connection: {_esc(str(fetch_dbg['error']))}")
                st = fetch_dbg.get("status")
                if st not in (None, ""):
                    detail_parts.append(f"HTTP status {_esc(str(st))}")
                if fetch_dbg.get("url"):
                    detail_parts.append(f"last request URL: {_esc(str(fetch_dbg['url']))}")
                detail = ("<br><small>" + " — ".join(detail_parts) + "</small>") if detail_parts else ""
                display_body_inner = (
                    '<div class="alert alert-danger" style="margin:16px;">'
                    f"Could not load Odoo HTML from upstream endpoint <code>{upstream_origin}</code>. "
                    "The display shell is active, but the server-side fetch got no HTML."
                    f"{detail}"
                    "<br><small>Check that Odoo is listening on that host/port. "
                    "If Django runs in Docker, use <code>http://host.docker.internal:8069/…</code> "
                    "or the compose service name (e.g. <code>http://odoo:8069/…</code>) in "
                    "<strong>PassThroughEndpoint</strong> instead of <code>localhost</code>.</small>"
                    "</div>"
                )

        display_head_inner = self._rewrite_web_paths_for_display_shell(
            display_head_inner, seg
        )
        display_body_inner = self._rewrite_web_paths_for_display_shell(
            display_body_inner, seg
        )
        display_head_inner = self._rewrite_absolute_polysaas_host_paths(
            display_head_inner, request.get_host(), proxy_prefix
        )
        display_body_inner = self._rewrite_absolute_polysaas_host_paths(
            display_body_inner, request.get_host(), proxy_prefix
        )

        # Prepend an early fetch/XHR shim to display_head_inner so it runs BEFORE
        # Odoo's inline scripts (especially odoo.reloadMenus() and the menu load fetch).
        # Without this, those calls go to the PolySaaS host before the full shim in
        # extrajs has a chance to patch fetch, causing 404s that break Owl boot.
        if endpoint is not None:
            _parsed = urlparse(endpoint.endpoint_url)
            _base = f"{_parsed.scheme}://{_parsed.netloc}"
            _early_shim = f"""<script data-polysaas-early-shim="1">
(function(){{
'use strict';
var PROXY={json.dumps(proxy_prefix)};
var B={json.dumps(_base)};
function _toProxy(u){{
    if(!u||typeof u!=='string')return u;
    if(u.indexOf(B)===0)return PROXY+u.slice(B.length);
    if(u.charAt(0)==='/'&&!u.startsWith(PROXY)){{
        if(u.startsWith('/web/')||u.startsWith('/odoo/')||u.startsWith('/bus/')||
           u.startsWith('/websocket')||u.startsWith('/mail/')||u.startsWith('/jsonrpc')||
           u.startsWith('/longpolling/')||u.startsWith('/website/')){{
            return PROXY+u;
        }}
    }}
    return u;
}}
var _f=window.fetch;
window.fetch=function(input,init){{
    if(typeof input==='string')input=_toProxy(input);
    else if(typeof Request!=='undefined'&&input instanceof Request){{var n=_toProxy(input.url);if(n!==input.url)input=new Request(n,input);}}
    return _f.call(this,input,init);
}};
var _x=XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open=function(){{
    var a=Array.prototype.slice.call(arguments);
    a[1]=_toProxy(a[1]);
    return _x.apply(this,a);
}};
console.log('[PolySaaS] Early fetch/XHR shim active, proxy='+PROXY);
}})();
</script>
"""
            display_head_inner = _early_shim + display_head_inner

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
                "display_odoo_pt_prefix": proxy_prefix,
                # Odoo 18 mounts nodes on document.body — display.html hijacks appendChild.
                "display_enable_odoo_body_scope": True,
                "display_shell_footer": (
                    f"Odoo passthrough ({seg}): head/scripts load here; "
                    f"Discuss shows “Inbox” like native Odoo. Proxy prefix {proxy_prefix}/"
                ),
            },
        )
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response

    @staticmethod
    def _rewrite_web_paths_for_display_shell(html: str, seg: str = "odoo") -> str:
        """Quoted /web/ and /website/ -> /pt/admin/<seg>/..."""
        if not html:
            return html
        proxy_web = f"/pt/admin/{seg}/web/"
        proxy_site = f"/pt/admin/{seg}/website/"
        return (
            html.replace('"/web/', f'"{proxy_web}')
            .replace("'/web/", f"'{proxy_web}")
            .replace('"/website/', f'"{proxy_site}')
            .replace("'/website/", f"'{proxy_site}")
        )

    @staticmethod
    def _rewrite_absolute_polysaas_host_paths(
        html: str, public_host: str, proxy_prefix: str
    ) -> str:
        """
        With X-Forwarded-Host, Odoo often embeds absolute URLs like
        http://localhost:8000/web/... — the browser loads those against PolySaaS without
        the passthrough prefix and assets 404; Owl never boots (blank shell).
        """
        if not html or not public_host or not proxy_prefix:
            return html
        ph = public_host.strip().lower()
        out = html
        for scheme in ("http", "https"):
            base = f"{scheme}://{ph}"
            pairs = (
                (f"{base}/web/", f"{base}{proxy_prefix}/web/"),
                (f"{base}/web?", f"{base}{proxy_prefix}/web?"),
                (f"{base}/odoo/", f"{base}{proxy_prefix}/odoo/"),
                (f"{base}/bus/", f"{base}{proxy_prefix}/bus/"),
                (f"{base}/websocket", f"{base}{proxy_prefix}/websocket"),
                (f"{base}/longpolling/", f"{base}{proxy_prefix}/longpolling/"),
                (f"{base}/website/", f"{base}{proxy_prefix}/website/"),
            )
            for old, new in pairs:
                if old in out:
                    out = out.replace(old, new)
        return out

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
            if not ta:
                return {}
            extra = ta.extra_config if isinstance(ta.extra_config, dict) else {}

            # TEMP: skip 1h session cache — it may still be another Odoo user from before admin/admin.
            # After revert to extra_config credentials, restore the cached-session block below.
            # session_id = ta.extra_config.get("odoo_session_id")
            # session_time = ta.extra_config.get("odoo_session_time", 0)
            # if session_id and (time.time() - session_time < 3600):
            #     return {"session_id": session_id}

            # TEMP (explicit user request): sidebar passthrough always JSON-RPC logs in as Odoo
            # admin/admin so you can reset Discuss/history on that account. Revert to
            # extra_config odoo_login / odoo_password when done.
            login_id = "admin"
            password = "admin"
            db_name = extra.get("odoo_db") or "odoo"

            # Resolve Odoo base URL from the PassThroughEndpoint (query from public schema)
            odoo_url = 'http://localhost:8069'
            try:
                from django.db import connection
                from dose.models import PassThroughEndpoint
                with connection.cursor() as cursor:
                    cursor.execute("SET search_path TO public;")
                    ep = PassThroughEndpoint.objects.filter(
                        trigger_path__iexact="odoo", is_enabled=True
                    ).order_by("-id").first()
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
                    if not isinstance(ta.extra_config, dict):
                        ta.extra_config = {}
                    ta.extra_config["odoo_session_id"] = sid
                    ta.extra_config["odoo_session_time"] = time.time()
                    ta.save(update_fields=["extra_config"])
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
        print(f"[ODOO HANDLER] Processing HTML for {endpoint_url}")

        if not endpoint_url:
            print("[ODOO HANDLER] No endpoint_url - returning raw HTML")
            return html_str, None

        parsed      = urlparse(endpoint_url.rstrip('/'))
        base_origin = f"{parsed.scheme}://{parsed.netloc}"
        hostname    = parsed.netloc  # e.g., polysaas-odoo2.onrender.com
        proxy_prefix = f'/pt/admin/{hostname}'
        print(f"[ODOO HANDLER] proxy_prefix={proxy_prefix}, base_origin={base_origin}")

        session_id = (self.get_upstream_cookies(request) or {}).get('session_id') or ''

        html_str = self._strip_base_tags(html_str)
        html_str = self._strip_meta_redirects(html_str)
        html_str = self._strip_csp(html_str)
        # Rewrite initial HTML asset paths BEFORE the JS shim runs.
        # <link> and <script> tags are fetched by the browser before JS executes, so we must
        # rewrite them server-side to route through our proxy.
        html_str = self._rewrite_static_paths(html_str, proxy_prefix=proxy_prefix, base_origin=base_origin)
        html_str = self._inject_client_shim(html_str, base_origin, session_id=session_id, proxy_prefix=proxy_prefix)

        print(f"[ODOO HANDLER] HTML processing complete")
        return html_str, None

    def _rewrite_static_paths(self, html, proxy_prefix='/pt/admin/odoo', base_origin=''):
        """
        Rewrite src/href/data-src/srcset attributes in <link>/<script>/<img> tags.
        
        Strategy:
        1. Odoo native paths (/web/, /odoo/, /bus/, etc.) -> route through proxy
        2. Other relative paths (/images/, /static/, etc.) -> make absolute with upstream origin
        """
        import re

        def _rewrite_path(path):
            """Rewrite a single path."""
            if not path or not path.startswith('/'):
                return path
            # Already proxied — never double-rewrite
            if path.startswith('/pt/'):
                return path
            # Odoo native paths -> proxy
            if (
                path.startswith('/web/')
                or path.startswith('/website/')
                or path.startswith('/odoo/')
                or path.startswith('/bus/')
                or path.startswith('/websocket')
            ):
                new_path = proxy_prefix + path
                print(f"[ODOO REWRITE] {path} -> {new_path}")
                return new_path
            # Other relative paths -> absolute upstream URL
            if base_origin:
                new_path = base_origin + path
                print(f"[ODOO REWRITE] {path} -> {new_path}")
                return new_path
            return path

        # 1. Rewrite standard attributes: href="...", src="...", action="..."
        # Match ALL relative paths starting with / (not just Odoo-specific ones)
        def _rewrite_attr(m):
            prefix = m.group(1)  # e.g., 'src="' or "src='"
            path = m.group(2)
            return prefix + _rewrite_path(path)

        html = re.sub(
            r'((?:href|src|action)=["\'])(/[^"\']+)',
            _rewrite_attr, html, flags=re.IGNORECASE,
        )

        # 2. Rewrite data-src (lazy loading) and data-original (some frameworks)
        html = re.sub(
            r'((?:data-src|data-original)=["\'])(/[^"\']+)',
            _rewrite_attr, html, flags=re.IGNORECASE,
        )

        # 3. Rewrite srcset (responsive images) - handles comma-separated URLs
        def _rewrite_srcset(m):
            prefix = m.group(1)
            srcset = m.group(2)
            # srcset format: "url1 1x, url2 2x" or "url1 100w, url2 200w"
            parts = []
            for part in srcset.split(','):
                part = part.strip()
                if not part:
                    continue
                # Extract URL and descriptor (e.g., "1x" or "100w")
                space_idx = part.find(' ')
                if space_idx > 0:
                    url = part[:space_idx]
                    descriptor = part[space_idx:]
                else:
                    url = part
                    descriptor = ''
                # Rewrite the URL if it matches
                if url.startswith('/'):
                    url = _rewrite_path(url)
                parts.append(url + descriptor)
            return prefix + ', '.join(parts)

        html = re.sub(
            r'(srcset=["\'])([^"\']+)',
            _rewrite_srcset, html, flags=re.IGNORECASE,
        )

        # 4. Rewrite inline style="background-image:url(...)" and similar
        def _rewrite_inline_style(m):
            prefix = m.group(1)  # style="... or style='
            style_val = m.group(2)
            # Rewrite url() inside the style value
            def _rewrite_style_url(url_m):
                quote = url_m.group(1) or ''
                path = url_m.group(2)
                close = url_m.group(3) or ''
                return f'url({quote}{_rewrite_path(path)}{close})'

            style_val = re.sub(
                r'url\((["\']?)(/[^)"\']*)(["\']?)\)',
                _rewrite_style_url, style_val,
            )
            return prefix + style_val

        html = re.sub(
            r'(style=["\'])([^"\']*url\([^"\']*)',
            _rewrite_inline_style, html, flags=re.IGNORECASE,
        )

        # 5. Rewrite url(...) inside <style> blocks (covers @font-face, background-image)
        def _rewrite_css_url(m):
            quote = m.group(1) or ''
            path = m.group(2)
            close = m.group(3) or ''
            return f'url({quote}{_rewrite_path(path)}{close})'

        html = re.sub(
            r'url\((["\']?)(/(?:web|website|odoo|bus|websocket)[^)"\']*)(["\']?)\)',
            _rewrite_css_url, html, flags=re.IGNORECASE,
        )

        # 6. Rewrite onsubmit inline JS containing this.action = '<path>'
        # Odoo login form: onsubmit="this.action = '/web/login' + location.hash"
        # Without this, onsubmit fires first and resets the correctly-rewritten action
        # back to the native path, bypassing the proxy and hitting Django's CSRF check.
        html = re.sub(
            r"(onsubmit=[\"'][^\"']*this\.action\s*=\s*')(/[^']+)(')",
            lambda m: m.group(1) + _rewrite_path(m.group(2)) + m.group(3),
            html,
            flags=re.IGNORECASE,
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

    def _inject_client_shim(self, html, base_origin, session_id='', proxy_prefix='/pt/admin/odoo'):
        import time
        base_json    = json.dumps(base_origin)
        session_json = json.dumps(session_id)
        proxy_json   = json.dumps(proxy_prefix)
        ts_json      = json.dumps(str(int(time.time())))

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
var TS = TS_JSON;        // timestamp to verify fresh code
var O = window.location.origin;
var SCOPE_SELECTOR = '.polysaas-passthrough-scope';

console.log('[PolySaaS Odoo] Shim v' + TS + ' starting, PROXY=' + PROXY + ', upstream=' + B + ', origin=' + O);

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

// Patch location.href AND pathname getters so Odoo's router sees the upstream
// path (stripped of proxy prefix), not /pt/admin/<host>/...
// Without this Odoo's Owl router sees an unknown route and renders nothing.
try {
    var hrefDesc = Object.getOwnPropertyDescriptor(Location.prototype, 'href');
    var pathnameDesc = Object.getOwnPropertyDescriptor(Location.prototype, 'pathname');
    function _stripProxy(raw) {
        if (raw && raw.indexOf(PROXY) === 0) return raw.slice(PROXY.length) || '/';
        return raw;
    }
    if (hrefDesc && hrefDesc.get && hrefDesc.set) {
        Object.defineProperty(Location.prototype, 'href', {
            get: function() {
                var raw = hrefDesc.get.call(this);
                // Strip proxy prefix from the path portion so Odoo reads the upstream URL
                try {
                    var u = new URL(raw);
                    u.pathname = _stripProxy(u.pathname);
                    return u.toString();
                } catch(e2) { return raw; }
            },
            set: function(v) {
                return hrefDesc.set.call(this, guardUrl(v));
            },
            configurable: true,
            enumerable: true
        });
    }
    if (pathnameDesc && pathnameDesc.get) {
        Object.defineProperty(Location.prototype, 'pathname', {
            get: function() {
                return _stripProxy(pathnameDesc.get.call(this));
            },
            set: pathnameDesc.set,
            configurable: true,
            enumerable: true
        });
    }
    console.log('[PolySaaS Odoo] location.href/pathname getters patched — router sees upstream path');
} catch(e) {
    console.warn('[PolySaaS Odoo] Could not patch location.href/pathname:', e);
}

// ═══════════════════════════════════════════════════════════════════════════
// 8. FORM SUBMISSION INTERCEPTION
// Odoo's Owl-rendered login form sets action="/web/login" in its component
// template — not in the server HTML we rewrite. Without this, the form
// submits directly to Django (bypassing the proxy) and hits CSRF rejection.
// ═══════════════════════════════════════════════════════════════════════════
document.addEventListener('submit', function(e) {
    var form = e.target;
    if (!form || form.tagName !== 'FORM') return;
    var rawAction = form.action || '';
    var proxied = toProxy(rawAction);
    if (proxied !== rawAction) {
        console.log('[PolySaaS Odoo] Form action rewrite:', rawAction, '->', proxied);
        form.setAttribute('action', proxied);
    }
}, true);

// ═══════════════════════════════════════════════════════════════════════════
// 9. ADAPTIVE UI - Make Odoo think it has the scope's dimensions
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
        patch = patch.replace('TS_JSON', ts_json)
        
        return html.replace('<head>', '<head>' + patch)

    def rewrite_upstream_body(self, body, ct, request, endpoint_url=None, upstream_path=None):
        """
        Server-side body rewriting for Odoo.
        Intercepts JavaScript bundles to redirect Owl's mount target.
        """
        # Derive proxy prefix from endpoint_url
        proxy_prefix = '/pt/admin/odoo'  # fallback
        if endpoint_url:
            from urllib.parse import urlparse
            parsed = urlparse(endpoint_url.rstrip('/'))
            proxy_prefix = f'/pt/admin/{parsed.netloc}'
        
        if 'javascript' in ct or 'css' in ct:
            try:
                text = body.decode('utf-8', errors='ignore')
                print(f"[ODOO REWRITE] Processing {ct} with proxy_prefix={proxy_prefix}")
                # Owl's mount target replacement.
                # Odoo 17 style: app.mount(document.body)       → matches .mount(document.body
                # Odoo 18 style: mount(WebClient, document.body) → matches ,document.body,
                # Both are replaced so the Owl root lands in our scope div, not in body.
                SCOPE = '.polysaas-passthrough-scope'
                SCOPE_JS = f'(document.querySelector("{SCOPE}")||document.body)'
                # Odoo 17 / Owl method call pattern
                patched = text.replace(
                    '.mount(document.body', f'.mount({SCOPE_JS}'
                )
                # Odoo 18 / standalone mount(Component, document.body, config) pattern
                patched = patched.replace(
                    ',document.body,', f',{SCOPE_JS},'
                )

                def _proxy_css_url(m):
                    quote = m.group(1) or ''
                    path  = m.group(2)
                    close = m.group(3) or ''
                    if path.startswith('/web/') or path.startswith('/odoo/') or path.startswith('/bus/') or path.startswith('/websocket'):
                        new_path = proxy_prefix + path
                        print(f"[ODOO REWRITE] CSS/JS url(): {path} -> {new_path}")
                        return f'url({quote}{new_path}{close})'
                    return f'url({quote}{path}{close})'

                patched = re.sub(
                    r'url\(([\"\"]?)(/(?:web|odoo|bus|websocket)/[^)\"\']*)([\"\']?)\)',
                    _proxy_css_url, patched,
                )

                # === FIX WEBSOCKET 404 - Force Odoo to use proxied WebSocket path ===
                # Use word-boundary regex so we only replace /websocket as a standalone
                # path component, not inside /bus/websocket_worker_bundle.
                if '/websocket' in patched:
                    patched = re.sub(
                        r'(?<!/odoo)/websocket(?!_)',
                        proxy_prefix + '/websocket',
                        patched,
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

    def postprocess_upstream_response(
        self,
        resp,
        request,
        *,
        endpoint_url,
        target_url,
        upstream_path,
        outbound_headers,
        upstream_cookies,
    ):
        """
        Odoo-specific upstream normalization belongs here, not in the shared forwarder.
        """
        print("=== ODOO COMPREHENSIVE FIX DEBUG ===")
        print("Status:", resp.status_code)
        print("Content-Type:", resp.headers.get('content-type'))
        print("Content-Length:", len(resp.content) if resp.content else 0)
        print("Location header:", resp.headers.get('Location', 'NONE'))

        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get('Location', '')
            print(f"=== ODOO REDIRECT: {resp.status_code} -> {location} ===")
            if location and (location.startswith('/odoo') or location.startswith('/web')):
                parsed = urlparse(endpoint_url)
                follow_url = f"{parsed.scheme}://{parsed.netloc}{location}"
                print(f"=== ODOO: Following redirect to {follow_url} ===")
                try:
                    follow_resp = requests.get(
                        follow_url,
                        headers=outbound_headers,
                        cookies=upstream_cookies,
                        allow_redirects=True,
                        timeout=60,
                    )
                    resp = follow_resp
                    print(f"=== ODOO: Followed redirect, final status: {resp.status_code} ===")
                except Exception as follow_exc:
                    print(f"=== ODOO: Failed to follow redirect: {follow_exc} ===")

        # HTML path rewriting is handled exclusively by process_html_response/_rewrite_static_paths.
        # Do NOT do byte-string replacements here — they run before process_html_response
        # and cause double-rewriting (path gets proxied twice → upstream URL gets proxy prefix embedded).

        print("Body preview (first 400 chars):")
        print(repr(resp.content[:400]) if resp.content else "EMPTY BODY")
        print("=== END ODOO DEBUG ===")
        return resp

