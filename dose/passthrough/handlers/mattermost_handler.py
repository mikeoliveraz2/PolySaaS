# dose/passthrough/handlers/mattermost_handler.py
"""Mattermost SPA passthrough: root-relative /api, /static, etc. must go under /pt/... prefix."""

import json
import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class MattermostPassthroughHandler:
    """
    The HTML shell is served from Django; JS bundles use absolute paths like /api/v4/..., which
    would hit the PolySaaS host without a prefix. We inject a fetch/XHR/WebSocket shim and point
    static assets at the real Mattermost origin (same pattern as Nextcloud).
    """

    def process_html_response(self, html_str, request, endpoint_url=None, *args, **kwargs):
        logger.info("[MATTERMOST HANDLER] Processing HTML shell")

        if not endpoint_url:
            return html_str, None

        origin = endpoint_url.rstrip("/")
        parsed = urlparse(origin)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"

        passthrough_prefix = self._passthrough_prefix(request)
        site_path_prefix = self._site_path_prefix(endpoint_url)

        html_str = self._rewrite_asset_tags(html_str, base_origin, site_path_prefix)
        html_str = self._inject_client_shim(
            html_str, passthrough_prefix, base_origin, site_path_prefix
        )

        return html_str, None

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

    def _rewrite_asset_tags(self, html, base_origin, site_path_prefix=""):
        """Load CSS/JS/fonts from Mattermost origin so large bundles skip Django."""

        pref = (site_path_prefix or "").rstrip("/")

        def mm_install_tail(url_path):
            """Strip Mattermost subpath so /mattermost/static matches /static rules."""
            if not pref:
                return url_path.split("?")[0].lower()
            uq = url_path.split("?")[0]
            if uq == pref or uq.lower() == pref.lower():
                return "/"
            low = uq.lower()
            pl = pref.lower()
            if low.startswith(pl + "/"):
                return uq[len(pref) :].split("?")[0].lower()
            return low

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
            path_only = mm_install_tail(url)
            if (
                path_only.startswith("/static/")
                or path_only.startswith("/plugins/")
                or path_only.startswith("/files/")
                or path_only.startswith("/images/")
                or path_only == "/favicon.ico"
            ):
                return f"{attr}={quote}{base_origin}{url}{quote}"
            return match.group(0)

        pattern = r'(src|href)=([\"\'])(/[^\"\']*?)\2'
        return re.sub(pattern, rewrite_attr, html)

    def _inject_client_shim(self, html, passthrough_prefix, base_origin, site_path_prefix=""):
        prefix_json = json.dumps(passthrough_prefix)
        base_json = json.dumps(base_origin)
        mm_json = json.dumps((site_path_prefix or "").rstrip("/"))
        patch = f"""
<script data-polysaas-mattermost-shim="1">
(function() {{
var P = {prefix_json};
var B = {base_json};
var M = {mm_json};
var O = window.location.origin;
function stripMmSubpath(s) {{
  if (!M) return s;
  if (s === M || s.startsWith(M + '/')) return (s === M) ? '/' : s.slice(M.length);
  return s;
}}
function absUrl(s) {{
  if (typeof s !== 'string') return s;
  if (s.startsWith(O + '/') || s === O) {{
    s = (s === O) ? '/' : s.slice(O.length);
  }} else if (s.startsWith('http:') || s.startsWith('https:') || s.startsWith('//')) {{
    if (B && (s === B || s.startsWith(B + '/'))) return s;
    return s;
  }}
  if (!s || s.startsWith('data:') || s.startsWith('blob:')) return s;
  if (s === P || s.startsWith(P + '/')) return s;
  if (s.charAt(0) !== '/') return s;
  s = stripMmSubpath(s);
  if (s.charAt(0) !== '/') return s;
  if (/^\\/(api)\\b/.test(s) || s.startsWith('/api?')) return P + s;
  if (/^\\/(static|plugins|files|images)\\b/.test(s) || s === '/favicon.ico' || s.startsWith('/_redirects')) return B + (M || '') + s;
  return s;
}}
var _f = window.fetch;
window.fetch = function(input, init) {{
  if (typeof input === 'string') input = absUrl(input);
  else if (typeof Request !== 'undefined' && input instanceof Request) {{
    var u = absUrl(input.url);
    if (u !== input.url) input = new Request(u, input);
  }}
  return _f.call(this, input, init);
}};
var _xo = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(method, url) {{
  var rest = Array.prototype.slice.call(arguments, 2);
  return _xo.apply(this, [method, absUrl(url)].concat(rest));
}};
var _WS = WebSocket;
window.WebSocket = function(url, protocols) {{
  if (typeof url === 'string') {{
    url = absUrl(url);
    if (url.charAt(0) === '/' && url.indexOf('/api/') !== -1) {{
      var pr = location.protocol === 'https:' ? 'wss:' : 'ws:';
      url = pr + '//' + location.host + url;
    }}
  }}
  return protocols === undefined ? new _WS(url) : new _WS(url, protocols);
}};
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

    def rewrite_upstream_body(
        self,
        body: bytes,
        content_type: str,
        request,
        endpoint_url=None,
        upstream_path: str = "/",
    ):
        """
        Patch JSON from /api/v4/config/client so SiteURL and websocket URLs point at this
        passthrough prefix; otherwise the SPA keeps calling the raw upstream host.
        """
        if not endpoint_url:
            return None
        ct = (content_type or "").split(";")[0].strip().lower()
        if ct != "application/json":
            return None
        path_only = (upstream_path or "").split("?")[0]
        if not path_only.startswith("/api/v4/config/client"):
            return None
        try:
            text = body.decode("utf-8")
            data = json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.warning("[MATTERMOST HANDLER] JSON rewrite skip: %s", e)
            return None
        if not isinstance(data, dict):
            return None

        prefix = self._passthrough_prefix(request)
        public_root = request.build_absolute_uri(prefix).split("?")[0].rstrip("/")

        ep = urlparse(endpoint_url.rstrip("/"))
        ws_scheme = "wss" if request.is_secure() else "ws"
        ws_public = f"{ws_scheme}://{request.get_host()}{prefix}/api/v4/websocket"

        def _same_upstream_host(url_str):
            if not url_str or not isinstance(url_str, str):
                return False
            try:
                p = urlparse(url_str)
                return p.netloc == ep.netloc
            except Exception:
                return False

        changed = False
        site_before = data.get("SiteURL")
        site = site_before
        if site and _same_upstream_host(site):
            data["SiteURL"] = public_root
            changed = True

        for key in ("WebsocketURL", "WebsocketUrl", "WebsocketSecureURL"):
            val = data.get(key)
            if val and isinstance(val, str) and _same_upstream_host(val):
                data[key] = ws_public
                changed = True

        if site_before and not changed:
            print(
                f"[MATTERMOST HANDLER] config/client SiteURL not patched "
                f"(endpoint host {ep.netloc!r} vs response {site_before!r}) — check PassThrough URL vs Mattermost Site URL"
            )

        if not changed:
            return None

        out = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        msg = f"[MATTERMOST HANDLER] Patched config/client SiteURL {site_before!r} -> {public_root!r} prefix={prefix!r}"
        print(msg)
        logger.info(msg)
        return out.encode("utf-8")
