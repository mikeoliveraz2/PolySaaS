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
    "js mjs css map woff woff2 ttf eot otf png jpg jpeg gif svg ico webp json wasm xml".split()
)

# Root-relative paths in Nextcloud HTML that must be prefixed with /pt/admin/{app}/…
_NC_PROXY_PATH_PREFIXES = (
    "/index.php/",
    "/index.php?",
    "/core/",
    "/apps/",
    "/ocs/",
    "/remote.php/",
    "/dav/",
    "/dist/",
    "/css/",
    "/js/",
    "/custom/",
    "/svg/",
    "/vendor/",
    "/themes/",
    "/settings/",
    "/avatar/",
    "/heartbeat",
    "/login",
    "/login/v2/",
    "/status.php",
    "/cron.php",
    "/appdata_",
    # Core UI + search + contacts (must hit proxy or browser gets Django HTML → MIME errors on .mjs)
    "/contactsmenu/",
    "/autocomplete/",
    "/unifiedsearch/",
    "/csrftoken",
)
_NC_PROXY_EXACT_PATHS = frozenset(
    {"/login", "/index.php", "/heartbeat", "/status.php", "/cron.php"}
)

# /pt/... without /pt/admin/<trigger>/ (wrong webroot depth)
_NC_PARTIAL_PT_PREFIXES = (
    "/pt/index.php/",
    "/pt/login",
    "/pt/ocs/",
    "/pt/remote.php/",
    "/pt/apps/",
    "/pt/core/",
    "/pt/avatar/",
    "/pt/heartbeat",
    "/pt/dist/",
    "/pt/css/",
    "/pt/js/",
    "/pt/vendor/",
    "/pt/svg/",
    "/pt/custom/",
    "/pt/themes/",
    "/pt/settings/",
    "/pt/dav/",
    "/pt/cron.php",
    "/pt/status.php",
    "/pt/contactsmenu/",
    "/pt/autocomplete/",
    "/pt/unifiedsearch/",
)


def _nc_proxy_prefix_from_endpoint(endpoint) -> str:
    seg = (
        (getattr(endpoint, "trigger_path", None) or "nextcloud")
        .strip("/")
        .lower()
        .split("/")[-1]
        .replace("-", "_")
    )
    return f"/pt/admin/{seg}"


def _nc_netloc_variants(endpoint_url: str) -> tuple:
    """Host:port forms Nextcloud may use in redirects (localhost vs 127.0.0.1)."""
    if not endpoint_url:
        return ("localhost:8888", "127.0.0.1:8888")
    n = urlparse(endpoint_url).netloc
    if not n:
        return ("localhost:8888", "127.0.0.1:8888")
    out = {n}
    if "localhost" in n:
        out.add(n.replace("localhost", "127.0.0.1", 1))
    if "127.0.0.1" in n:
        out.add(n.replace("127.0.0.1", "localhost", 1))
    return tuple(out)


def _nc_upstream_base_aliases(base: str) -> list:
    """http://localhost:8888 vs http://127.0.0.1:8888 both appear in NC HTML/JSON."""
    b = (base or "").rstrip("/")
    if not b:
        return []
    out = {b}
    if "localhost" in b:
        out.add(b.replace("localhost", "127.0.0.1", 1))
    if "127.0.0.1" in b:
        out.add(b.replace("127.0.0.1", "localhost", 1))
    return list(out)


def _nc_root_path_should_proxy(path: str, proxy_prefix: str) -> bool:
    """True if path is a Nextcloud root-relative URL that should be served under proxy_prefix."""
    if not path or not path.startswith("/"):
        return False
    if path.startswith(proxy_prefix):
        return False
    # NC app root in generated links
    if path == "/":
        return True
    if path.startswith("/index.php?"):
        return True
    p = path.rstrip("/") or "/"
    if p in _NC_PROXY_EXACT_PATHS:
        return True
    for pfx in _NC_PROXY_PATH_PREFIXES:
        if path.startswith(pfx) or path == pfx.rstrip("/"):
            return True
    return False


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


def _nextcloud_session_cookie_present(request) -> bool:
    """
    True if the browser likely holds an upstream Nextcloud session.
    Cookie names vary by version (oc<instanceid>, oc_sessionPassphrase, etc.).
    """
    if not request or not getattr(request, "COOKIES", None):
        return False
    for name in request.COOKIES:
        low = name.lower()
        if low in ("nc_session_id", "nc_username", "oc_sessionpassphrase"):
            return True
        if low.startswith("__host-nc") or low.startswith("__secure-nc"):
            return True
        if name.startswith("oc") and len(name) >= 12:
            return True
    return False


def _nc_shell_path_needs_nc_session(path_with_possible_qs: str) -> bool:
    """HTML paths we server-fetch; without session cookies upstream often embeds null currentUser."""
    p = (path_with_possible_qs or "").split("?")[0].rstrip("/") or "/"
    if p in ("/", "/index.php"):
        return True
    if "/apps/" in p:
        return True
    return False


class NextcloudPassthroughHandler:
    """
    Passthrough handler for Nextcloud.
    Implements try_root_display_shell_response so the middleware wraps HTML responses
    in admin/display.html (the same shell used for Odoo and Mattermost).
    """

    def filter_cookies_for_upstream(self, request, cookies: dict) -> dict:
        """
        Nextcloud skips SameSite probe cookies when unrelated cookies are present (e.g. Django
        session). Strip everything on GET to the login path so NC issues a fresh session and
        requesttoken; on other requests forward only oc* / nc_* cookies.
        """
        path = (request.path_info or request.path or "").lower()
        if request.method == "GET" and "login" in path:
            return {}
        return {k: v for k, v in cookies.items() if k.startswith("oc") or k.startswith("nc_")}

    def should_forward_set_cookie_headers(
        self,
        request,
        *,
        upstream_content_type=None,
        upstream_path=None,
        response_kind=None,
    ) -> bool:
        """
        Keep Nextcloud's session cookie aligned with the requesttoken embedded in HTML.
        Static asset responses can emit fresh session cookies that break that pairing.
        """
        if response_kind != "non-html":
            return True
        content_type = (upstream_content_type or "").lower()
        static_asset_types = (
            "application/javascript",
            "text/javascript",
            "text/css",
            "image/",
            "font/",
            "application/font-",
            "application/x-font-",
        )
        return not any(content_type.startswith(prefix) for prefix in static_asset_types)

    # ------------------------------------------------------------------
    # Incoming path rewrite (called by incoming_path_rewrite.apply_incoming_path_rewrites)
    # ------------------------------------------------------------------

    @staticmethod
    def _nc_incoming_rewrite_confidence(request, proxy_prefix: str) -> bool:
        ref = request.META.get("HTTP_REFERER", "") or ""
        if proxy_prefix in ref:
            return True
        if _nextcloud_session_cookie_present(request):
            return True
        return False

    def try_rewrite_incoming_path(self, request, endpoint) -> bool:
        """
        Map /pt/... (missing admin segment) and bare /core/, /apps/, … onto this endpoint's proxy prefix.
        """
        proxy_prefix = _nc_proxy_prefix_from_endpoint(endpoint)
        path = request.path_info

        if path.startswith("/pt/") and not path.startswith("/pt/admin/"):
            for pfx in _NC_PARTIAL_PT_PREFIXES:
                if path == pfx.rstrip("/") or path.startswith(pfx):
                    request.path_info = proxy_prefix + path[3:]
                    print(f"[NC-HANDLER] partial /pt/ rewrite → {request.path_info}")
                    return True
            return False

        if path.startswith("/pt/"):
            return False
        if path == "/" or not path.startswith("/"):
            return False
        if not _nc_root_path_should_proxy(path, proxy_prefix):
            return False
        if not self._nc_incoming_rewrite_confidence(request, proxy_prefix):
            return False

        request.path_info = proxy_prefix + path
        print(f"[NC-HANDLER] bare path rewrite → {request.path_info}")
        return True

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

        # Skip display shell for login page — let browser get session + requesttoken directly
        # from Nextcloud so they match. Server-side fetch creates a session mismatch.
        if upstream_subpath.rstrip("/") in ("/login", "/index.php/login"):
            return None

        from django.shortcuts import render

        display_head_inner = ""
        display_body_inner = ""
        upstream_set_cookies = []

        if endpoint is not None:
            _parsed = urlparse(endpoint.endpoint_url)
            _base = f"{_parsed.scheme}://{_parsed.netloc}"
            nc_netlocs = _nc_netloc_variants(endpoint.endpoint_url)

            fetch_path = upstream_subpath if upstream_subpath not in ("", "/") else "/"
            # Include query string so Nextcloud receives params like ?direct=1&user=admin.
            # Without this, fetching /login always returns the redirect to /login?direct=1
            # which the browser follows back to the same URL — causing ERR_TOO_MANY_REDIRECTS.
            qs = request.META.get("QUERY_STRING", "")
            if qs:
                fetch_path = fetch_path + "?" + qs

            # Cookie-name heuristics false-positive easily (any long "oc*" cookie). Verify with
            # OCS: unauthenticated HTML still boots the dashboard Vue with null currentUser.
            if _nc_shell_path_needs_nc_session(fetch_path):
                _fb = _base.replace("localhost", "127.0.0.1")
                if not NextcloudPassthroughHandler._nc_upstream_ocs_user_ok(_fb, request):
                    print("[NC_OCS] user probe failed — redirect to login")
                    print(
                        "[NC-HANDLER] OCS user probe failed — redirect to login "
                        "(bootstrap real NC session before display shell fetch)"
                    )
                    redir = proxy_prefix + "/login?direct=1"
                    if qs:
                        redir = redir + "&" + qs
                    return HttpResponseRedirect(redir)

            raw_html, upstream_set_cookies, fetch_dbg = self._fetch_nc_html(
                _base, fetch_path, proxy_prefix, request
            )

            # Root "/" sometimes returns empty or non-HTML; /index.php is a reliable entry.
            _fp0 = fetch_path.split("?")[0].rstrip("/") or "/"
            if (
                (not raw_html or not raw_html.strip())
                and _fp0 == "/"
                and not (raw_html or "").startswith("REDIRECT:")
            ):
                alt = "/index.php"
                if qs:
                    alt = alt + "?" + qs
                print(f"[NC_FETCH] Root returned empty HTML — retry fetch_path={alt!r}")
                raw_html, upstream_set_cookies, fetch_dbg = self._fetch_nc_html(
                    _base, alt, proxy_prefix, request
                )

            if (
                fetch_dbg
                and endpoint is not None
                and raw_html
                and not raw_html.startswith("REDIRECT:")
            ):
                from dose.passthrough.stream_debug import log_handler_fetched_html_if_debug

                log_handler_fetched_html_if_debug(
                    request,
                    endpoint,
                    phase="nextcloud_display_shell_fetch",
                    target_url=fetch_dbg["target_url"],
                    status_code=fetch_dbg["status"],
                    content_type=fetch_dbg.get("content_type", ""),
                    body_text=raw_html,
                    set_cookie_lines=fetch_dbg.get("set_cookie_lines") or [],
                )

            # If upstream redirected to a PolySaaS URL outside the proxy prefix → browser redirect
            redir = self._display_shell_redirect_from_fetch(
                raw_html, request, proxy_prefix, nc_netlocs
            )
            if redir is not None:
                # Forward Set-Cookie on redirects too (e.g. post-login redirect carries nc_session)
                self._apply_set_cookies(redir, upstream_set_cookies)
                return redir

            if raw_html and not raw_html.startswith("REDIRECT:"):
                # Extract <head> content — also grab data-requesttoken from the <head> tag itself.
                # Nextcloud's Vue login reads document.head.dataset.requesttoken for CSRF validation.
                # We only inject inner content so the attribute would be lost without this.
                m = re.search(r"<head([^>]*)>(.*?)</head>", raw_html, re.DOTALL | re.IGNORECASE)
                if m:
                    head_attrs = m.group(1)
                    head_raw = m.group(2).strip()
                    head_raw = self._strip_base_tags(head_raw)
                    head_raw = self._strip_csp_meta(head_raw)
                    display_head_inner = self._rewrite_nc_paths(head_raw, proxy_prefix, _base)

                    # -------------------------------------------------------
                    # Copy ALL data-* attributes from the Nextcloud <head> tag
                    # to document.head so Nextcloud's JS can read them.
                    #
                    # Nextcloud core reads (among others):
                    #   document.head.dataset.user           → OC.currentUser
                    #   document.head.dataset.uid            → user id
                    #   document.head.dataset.userDisplayname
                    #   document.head.dataset.requesttoken   → CSRF token
                    #   document.head.dataset.allowedAdminGroups
                    #   document.head.dataset.adminNonce / nonce
                    #
                    # Previously we only copied data-requesttoken, leaving every
                    # user-related attribute null → OC.getCurrentUser() = null → Vue crash.
                    # -------------------------------------------------------
                    data_attrs = re.findall(
                        r'\b(data-[a-z0-9_-]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\')',
                        head_attrs,
                        re.IGNORECASE,
                    )
                    if data_attrs:
                        js_parts = []
                        for attr_name, dq_val, sq_val in data_attrs:
                            val = dq_val if dq_val else sq_val
                            # Convert data-foo-bar to camelCase dataset key fooBar
                            key_parts = attr_name[5:].split("-")  # strip leading "data-"
                            dataset_key = key_parts[0] + "".join(
                                p.capitalize() for p in key_parts[1:]
                            )
                            escaped = val.replace("\\", "\\\\").replace('"', '\\"')
                            js_parts.append(
                                f'document.head.dataset["{dataset_key}"]="{escaped}";'
                            )
                        head_dataset_js = "\n".join(js_parts)
                        print(
                            f"[NC-HANDLER] Injecting {len(data_attrs)} head data-attrs: "
                            + ", ".join(a[0] for a in data_attrs[:8])
                        )
                        display_head_inner = (
                            f"<script>{head_dataset_js}</script>\n"
                            + display_head_inner
                        )

                # Extract <body> content, preserving id="body-login" for Vue mount
                m_body = re.search(r"<body([^>]*)>(.*?)</body>", raw_html, re.DOTALL | re.IGNORECASE)
                if m_body:
                    body_attrs = m_body.group(1).strip()
                    body_raw = m_body.group(2).strip()
                    body_rewritten = self._rewrite_nc_paths(body_raw, proxy_prefix, _base)
                    # Wrap in a div with the original body attributes (especially id="body-login")
                    # Vue's login component mounts on #body-login
                    display_body_inner = f'<div {body_attrs}>{body_rewritten}</div>'

            # Prepend early fetch/XHR shim so it runs before any Nextcloud inline scripts
            early_shim = self._build_early_shim(proxy_prefix, _base)
            display_head_inner = early_shim + display_head_inner

        if endpoint is None:
            shell_footer = "Nextcloud: no PassThroughEndpoint in context — check tenant schema."
        elif not (display_body_inner or "").strip():
            shell_footer = (
                "Nextcloud display shell: no body HTML extracted. "
                "Check console + server [NC_FETCH] lines; confirm endpoint_url and NC is up. "
                "Try opening /pt/admin/nextcloud/login/ in the same session."
            )
        else:
            shell_footer = (
                f"Nextcloud passthrough — endpoint {_base!s}, proxy {proxy_prefix}/"
            )

        response = render(
            request,
            "admin/display.html",
            {
                "display_head_inner": display_head_inner,
                "display_body_inner": display_body_inner,
                "service_name": "Nextcloud",
                "proxy_prefix": proxy_prefix,
                "display_enable_odoo_body_scope": False,
                "display_nextcloud_bucket": True,
                "display_shell_footer": shell_footer,
            },
        )
        # Forward Nextcloud session cookies (e.g. the session ID cookie that ties the
        # data-requesttoken in the HTML to the server-side session). Without this the
        # browser can't validate the CSRF token on form submission and login fails.
        self._apply_set_cookies(response, upstream_set_cookies)
        return response

    @staticmethod
    def _nc_upstream_ocs_user_ok(fetch_base: str, request) -> bool:
        """
        True if Nextcloud accepts the browser cookie jar as a logged-in user.
        Uses OCS; avoids false positives from unrelated cookies matching oc* heuristics.
        """
        import requests as _rq

        if not request or not getattr(request, "COOKIES", None):
            return False
        cookies = dict(request.COOKIES)
        headers = {
            "OCS-APIRequest": "true",
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        ua = request.META.get("HTTP_USER_AGENT")
        if ua:
            headers["User-Agent"] = ua
        ref = request.META.get("HTTP_REFERER")
        if ref:
            headers["Referer"] = ref
        al = request.META.get("HTTP_ACCEPT_LANGUAGE")
        if al:
            headers["Accept-Language"] = al
        url = fetch_base.rstrip("/") + "/ocs/v2.php/cloud/user"
        try:
            resp = _rq.get(
                url, headers=headers, cookies=cookies, allow_redirects=False, timeout=15
            )
        except Exception as exc:
            print(f"[NC_OCS] probe GET failed: {exc}")
            return False
        if resp.status_code != 200:
            print(f"[NC_OCS] probe status={resp.status_code} url={url!r}")
            return False
        try:
            payload = resp.json()
        except Exception:
            print("[NC_OCS] probe: response not JSON")
            return False
        ocs = payload.get("ocs") or {}
        meta = ocs.get("meta") or {}
        try:
            ocs_sc = int(meta.get("statuscode", 0))
        except (TypeError, ValueError):
            ocs_sc = 0
        if ocs_sc != 200:
            print(f"[NC_OCS] probe ocs.meta.statuscode={meta.get('statuscode')!r}")
            return False
        data = ocs.get("data")
        if not isinstance(data, dict):
            print("[NC_OCS] probe: missing ocs.data object")
            return False
        uid = data.get("id")
        if uid is None or uid == "":
            print("[NC_OCS] probe: ocs.data has no id")
            return False
        print(f"[NC_OCS] probe ok id={uid!r} url={url!r}")
        return True

    @staticmethod
    def _fetch_nc_html(base: str, path: str, proxy_prefix: str, request):
        """
        Fetch HTML from Nextcloud upstream.
        Returns a tuple (html_str, set_cookie_raw_list, debug_meta_or_none).

        KEY INSIGHT: When fetching via 'localhost', Nextcloud matches its OVERWRITEHOST
        setting and issues redirect loops back to the PolySaaS host. Fetching via
        '127.0.0.1' bypasses OVERWRITEHOST matching and returns HTML directly.
        We normalise 'localhost' → '127.0.0.1' before making any request.
        """
        import requests as _rq

        # Force IP address so Nextcloud's OVERWRITEHOST rule doesn't match.
        fetch_base = base.replace("localhost", "127.0.0.1")

        # Forward browser cookies so Nextcloud knows if the user is already authenticated.
        # Exception: the bare /login path with NO query string — forwarding cookies there
        # causes Nextcloud to redirect to /login?direct=1&user=admin (cross-origin), which
        # we then send to the browser, which comes back to the same bare /login, looping.
        # With a query string (?direct=1&user=admin), forwarding cookies is safe: Nextcloud
        # either serves the login form (unauthenticated) or redirects to dashboard (authenticated).
        _bare_login = path.split("?")[0].rstrip("/") in ("/login", "/index.php/login")
        _has_qs = "?" in path
        browser_cookies = {} if (_bare_login and not _has_qs) else (dict(request.COOKIES) if request else {})
        set_cookies = []  # collect Set-Cookie raw values to forward to the browser

        headers = {
            "Accept": "text/html,application/xhtml+xml",
            # Avoid upstream 304 with empty body — display shell needs full HTML to extract head/body.
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        if request:
            ua = request.META.get("HTTP_USER_AGENT")
            if ua:
                headers["User-Agent"] = ua
            else:
                headers["User-Agent"] = "Mozilla/5.0 (compatible; PolySaaS-Proxy/1.0)"
            ref = request.META.get("HTTP_REFERER")
            if ref:
                headers["Referer"] = ref
            al = request.META.get("HTTP_ACCEPT_LANGUAGE")
            headers["Accept-Language"] = al or "en-US,en;q=0.9"
            acc = request.META.get("HTTP_ACCEPT")
            if acc and "text/html" in acc:
                headers["Accept"] = acc
        else:
            headers["User-Agent"] = "Mozilla/5.0 (compatible; PolySaaS-Proxy/1.0)"
            headers["Accept-Language"] = "en-US,en;q=0.9"

        current_path = path
        for hop in range(6):
            url = fetch_base.rstrip("/") + current_path
            print(f"[NC_FETCH] Hop {hop}: GET {url}")
            try:
                resp = _rq.get(url, headers=headers, cookies=browser_cookies,
                               allow_redirects=False, timeout=30)
            except Exception as exc:
                print(f"[NC_FETCH] Request failed: {exc}")
                return "", set_cookies, None

            print(f"[NC_FETCH] Hop {hop}: Status {resp.status_code}")

            if resp.status_code == 304:
                sep = "&" if "?" in url else "?"
                bust_url = url + sep + "_polysaas_nc_fetch=1"
                print(f"[NC_FETCH] Hop {hop}: 304 — retry GET {bust_url}")
                try:
                    resp = _rq.get(
                        bust_url,
                        headers=headers,
                        cookies=browser_cookies,
                        allow_redirects=False,
                        timeout=30,
                    )
                    url = bust_url
                    print(f"[NC_FETCH] Hop {hop}: retry status {resp.status_code}")
                except Exception as exc:
                    print(f"[NC_FETCH] 304 retry failed: {exc}")

            # Accumulate Set-Cookie headers from every hop
            for _rh, _rv in resp.raw.headers.items():
                if _rh.lower() == "set-cookie":
                    set_cookies.append(_rv)

            if resp.status_code == 200:
                ct = resp.headers.get("Content-Type", "")
                if "text/html" in ct:
                    print(f"[NC_FETCH] Got HTML ({len(resp.content)} bytes)")
                    dbg = {
                        "target_url": url,
                        "status": 200,
                        "content_type": ct,
                        "set_cookie_lines": list(set_cookies),
                    }
                    return resp.text, set_cookies, dbg
                print(f"[NC_FETCH] Non-HTML content-type: {ct}")
                return "", set_cookies, None

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

                # Absolute URL — check if it's a same-origin redirect (could be localhost or 127.0.0.1)
                loc_parsed = urlparse(loc)
                loc_origin = f"{loc_parsed.scheme}://{loc_parsed.netloc}"
                # Treat localhost:8888 and 127.0.0.1:8888 as same origin
                nc_origins = (fetch_base, fetch_base.replace("127.0.0.1", "localhost"))
                if loc_origin not in nc_origins:
                    # Cross-origin redirect (e.g. to PolySaaS or external) — let caller handle
                    return f"REDIRECT:{resp.status_code}:{loc}", set_cookies, None
                # Same-origin absolute: extract path and continue fetching
                current_path = loc_parsed.path
                if loc_parsed.query:
                    current_path += "?" + loc_parsed.query
                continue

            # Any other status
            print(f"[NC_FETCH] Unexpected status {resp.status_code}")
            return "", set_cookies, None

        print("[NC_FETCH] Exceeded hop limit")
        return "", set_cookies, None

    @staticmethod
    def _apply_set_cookies(response, set_cookie_raw_list):
        """Copy raw Set-Cookie strings from upstream onto a Django response."""
        from http.cookies import SimpleCookie
        for raw in (set_cookie_raw_list or []):
            try:
                sc = SimpleCookie()
                sc.load(raw)
                for name, morsel in sc.items():
                    response.cookies[name] = morsel.value
                    response.cookies[name]["path"] = morsel.get("path") or "/"
                    response.cookies[name]["samesite"] = "Lax"
                    print(f"[NC_FETCH] Forwarding Set-Cookie to browser: {name}")
            except Exception as e:
                print(f"[NC_FETCH] Set-Cookie parse error: {e}")

    @staticmethod
    def _display_shell_redirect_from_fetch(raw_html, request, proxy_prefix, nc_netlocs):
        """
        _fetch_nc_html returns REDIRECT:status:url when upstream returns a redirect.
        This handles two cases:
        1. Nextcloud redirects to PolySaaS host (localhost:8000) with proxy prefix baked in
           → just use the path as-is
        2. Nextcloud redirects to its own origin (port from endpoint URL) without proxy prefix
           → prepend proxy_prefix so the browser goes through PolySaaS
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
        
        # Case 1: Redirect already has proxy prefix (old overwritewebroot behavior)
        if path.startswith(proxy_prefix):
            target = path
            if loc_parsed.query:
                target = f"{path}?{loc_parsed.query}"
            return HttpResponseRedirect(target)
        
        # Case 2: Redirect to Nextcloud's origin (e.g. http://127.0.0.1:8888/apps/dashboard/)
        # Convert to proxy path so browser stays in PolySaaS
        if loc_parsed.netloc in nc_netlocs:
            target = f"{proxy_prefix}{path}"
            if loc_parsed.query:
                target = f"{target}?{loc_parsed.query}"
            print(f"[NC_HANDLER] Redirect to NC origin -> rewriting to {target}")
            return HttpResponseRedirect(target)
        
        # Case 3: Redirect to PolySaaS origin without proxy prefix (shouldn't happen, but handle it)
        polysaas_host = request.get_host() if request else "localhost:8000"
        if loc_parsed.netloc == polysaas_host:
            # External redirect to PolySaaS — follow it as-is (might be /accounts/login/)
            target = path
            if loc_parsed.query:
                target = f"{path}?{loc_parsed.query}"
            return HttpResponseRedirect(target)
        
        # Unknown redirect destination — let it pass through
        print(f"[NC_HANDLER] Unknown redirect destination: {location}")
        return None

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

    def process_html_response(self, html_str, request, endpoint_url=None, *args, **kwargs):
        """Rewrite URLs in proxied HTML that bypasses the display shell."""
        if not endpoint_url:
            return html_str, None
        parsed = urlparse(endpoint_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        ep = getattr(request, "_passthrough_endpoint", None)
        proxy_prefix = (
            _nc_proxy_prefix_from_endpoint(ep) if ep is not None else "/pt/admin/nextcloud"
        )
        html_str = self._rewrite_nc_paths(html_str, proxy_prefix, base)
        
        # Inject shim + _oc_webroot at the START of <head>, BEFORE oc.js loads
        # This ensures _oc_webroot is set before Nextcloud reads it
        shim = self._build_early_shim(proxy_prefix, base)
        import re
        # Insert right after <head...>
        html_str = re.sub(
            r'(<head[^>]*>)',
            r'\1' + shim,
            html_str,
            count=1,
            flags=re.IGNORECASE
        )
        
        return html_str, None

    # ------------------------------------------------------------------
    # Server-side URL rewriting
    # ------------------------------------------------------------------

    def _rewrite_nc_paths(self, html: str, proxy_prefix: str, base: str) -> str:
        """
        Rewrite Nextcloud root-relative and upstream-absolute URLs so the browser loads
        assets and navigation through proxy_prefix. Covers srcset, lazy-load data attrs,
        and quoted url(...) in inline CSS where safe.

        Script bodies are excluded from bulk quoted-URL replacement: running
        html.replace('\"http://127.0.0.1:8888/', ...) across embedded JSON initial state
        breaks parsing and leaves OC.getCurrentUser() null (Vue crashes) even when OCS
        /cloud/user returns 200 for the same cookie jar.
        """

        base_aliases = _nc_upstream_base_aliases(base)

        def proxy_single(url: str) -> str:
            if not url:
                return url
            u = url.strip()
            if u.startswith("data:") or u.startswith("javascript:") or u.startswith("#"):
                return url
            for ab in base_aliases:
                if u.startswith(ab + "/"):
                    return proxy_prefix + u[len(ab) :]
            if _nc_root_path_should_proxy(u, proxy_prefix):
                return proxy_prefix + u
            return url

        def rewrite_srcset_list(val: str) -> str:
            parts_out = []
            for chunk in re.split(r"\s*,\s*", val):
                chunk = chunk.strip()
                if not chunk:
                    continue
                bits = chunk.split()
                u0 = proxy_single(bits[0])
                parts_out.append(" ".join([u0] + bits[1:]))
            return ", ".join(parts_out)

        def rewrite_attr_value(match):
            attr = match.group(1)
            quote = match.group(2)
            raw = match.group(3)
            al = attr.lower()
            if al in ("srcset", "data-srcset", "imagesrcset"):
                newv = rewrite_srcset_list(raw)
                if newv == raw:
                    return match.group(0)
                return f"{attr}={quote}{newv}{quote}"
            url = raw.strip()
            newu = proxy_single(url)
            if newu == url:
                return match.group(0)
            return f"{attr}={quote}{newu}{quote}"

        def rewrite_url_call(m):
            q, path = m.group(1), m.group(2).strip()
            if path.startswith("data:"):
                return m.group(0)
            newp = proxy_single(path)
            if newp == path:
                return m.group(0)
            return f"url({q}{newp}{q})"

        def rewrite_url_call_http(m):
            q, path = m.group(1), m.group(2).strip()
            if path.startswith("data:"):
                return m.group(0)
            newp = proxy_single(path)
            if newp == path:
                return m.group(0)
            return f"url({q}{newp}{q})"

        def rewrite_markup_segment(segment: str) -> str:
            """Attrs + root-relative url() + bulk quoted upstream URLs (safe outside scripts)."""
            h = segment
            multi_attrs = r"(?i)\b(srcset|data-srcset|imagesrcset)\s*=\s*([\"'])(.*?)\2"
            h = re.sub(multi_attrs, rewrite_attr_value, h, flags=re.DOTALL)
            single_attrs = (
                r"(?i)\b(href|src|action|data-url|data-href|data-link|data-src|data-lazy-src|"
                r"data-original|data-background-url|data-icon-url|poster)\s*=\s*([\"'])([^\"']*)\2"
            )
            h = re.sub(single_attrs, rewrite_attr_value, h)
            h = re.sub(
                r'url\(\s*([\"\'])(/[^\"\'\)]*)\1\s*\)',
                rewrite_url_call,
                h,
                flags=re.IGNORECASE,
            )
            h = re.sub(
                r'url\(\s*([\"\'])(https?://[^\"\'\)]*)\1\s*\)',
                rewrite_url_call_http,
                h,
                flags=re.IGNORECASE,
            )
            for ab in base_aliases:
                h = h.replace(f'"{ab}/', f'"{proxy_prefix}/')
                h = h.replace(f"'{ab}/", f"'{proxy_prefix}/")
            return h

        def rewrite_style_inner(inner: str) -> str:
            """CSS only: url() paths; never bulk-replace quoted JSON-like strings."""
            h = inner
            h = re.sub(
                r'url\(\s*([\"\'])(/[^\"\'\)]*)\1\s*\)',
                rewrite_url_call,
                h,
                flags=re.IGNORECASE,
            )
            h = re.sub(
                r'url\(\s*([\"\'])(https?://[^\"\'\)]*)\1\s*\)',
                rewrite_url_call_http,
                h,
                flags=re.IGNORECASE,
            )
            return h

        scripts: list[tuple[str, str, str]] = []

        def _stash_script(m: re.Match) -> str:
            scripts.append((m.group(1), m.group(2), m.group(3)))
            return f"__NCRW_SCRIPT_{len(scripts) - 1}__"

        # Unescaped </script> inside JS strings is rare in NC bundles; acceptable risk.
        html = re.sub(
            r"(?is)(<script\b[^>]*>)(.*?)(</script\s*>)",
            _stash_script,
            html,
        )

        styles: list[tuple[str, str, str]] = []

        def _stash_style(m: re.Match) -> str:
            styles.append((m.group(1), m.group(2), m.group(3)))
            return f"__NCRW_STYLE_{len(styles) - 1}__"

        html = re.sub(
            r"(?is)(<style\b[^>]*>)(.*?)(</style\s*>)",
            _stash_style,
            html,
        )

        html = rewrite_markup_segment(html)

        for i, (o, inn, c) in enumerate(styles):
            html = html.replace(f"__NCRW_STYLE_{i}__", o + rewrite_style_inner(inn) + c)

        for i, (o, inn, c) in enumerate(scripts):
            o_rw = rewrite_markup_segment(o)
            html = html.replace(f"__NCRW_SCRIPT_{i}__", o_rw + inn + c)

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
        Full client shim (aligned with Mattermost pattern): fetch, XHR, WebSocket,
        PolySaaS-path guard, script/link/img setters + setAttribute, OC.generateUrl,
        history, login form fixes.
        """
        nc_paths_js = json.dumps(
            list(dict.fromkeys(list(_NC_PROXY_PATH_PREFIXES) + ["/csrftoken"]))
        )
        return f"""<script data-polysaas-nc-shim="1">
// Set _oc_webroot BEFORE oc.js loads — Nextcloud reads this to build all URLs
window._oc_webroot={json.dumps(proxy_prefix)};
// Also set on documentElement for scripts that read it from there
document.documentElement.setAttribute('data-oc-webroot', {json.dumps(proxy_prefix)});
(function(){{
'use strict';
var PROXY={json.dumps(proxy_prefix)};
var BASE={json.dumps(base)};
var NC_PATHS={nc_paths_js};
var O=window.location.origin;
var PS_PREFIXES=['/static/admin/','/static/img/','/admin/','/dose/','/media/','/accounts/','/pt/','/favicon'];
function _isPS(p){{for(var i=0;i<PS_PREFIXES.length;i++){{if(p.startsWith(PS_PREFIXES[i]))return true;}}return false;}}

// Nextcloud often uses http://127.0.0.1:PORT in JSON while endpoint_url is localhost (or vice versa).
// Those absolute URLs must map to PROXY or fetch runs cross-origin from PolySaaS → currentUser stays null.
function _ncPort(pu){{return pu.port||(pu.protocol==='https:'?'443':'80');}}
function _ncSameUpstreamOrigin(u,b){{
    try{{
        if(u.protocol!==b.protocol)return false;
        var uh=u.hostname,bh=b.hostname;
        var loop=(uh==='localhost'||uh==='127.0.0.1')&&(bh==='localhost'||bh==='127.0.0.1');
        if(loop)return _ncPort(u)===_ncPort(b);
        return u.hostname===b.hostname&&_ncPort(u)===_ncPort(b);
    }}catch(e){{return false;}}
}}
function _absUpstreamToProxy(u){{
    if(!u||(u.indexOf('http:')!==0&&u.indexOf('https:')!==0))return null;
    try{{
        var uu=new URL(u);
        var bb=new URL(BASE.endsWith('/')?BASE:BASE+'/');
        if(!_ncSameUpstreamOrigin(uu,bb))return null;
        return PROXY+uu.pathname+(uu.search||'')+(uu.hash||'');
    }}catch(e){{return null;}}
}}

// Force-fix form actions after Vue renders — we know the correct action path
function _fixLoginForms() {{
    var forms = document.querySelectorAll('form');
    forms.forEach(function(form) {{
        var action = form.getAttribute('action') || form.action || '';
        // Fix any form that posts to /login without the proxy prefix
        if (action.indexOf('/login') !== -1 && action.indexOf(PROXY) === -1) {{
            form.action = PROXY + '/login';
            console.log('[PolySaaS] Fixed form action to:', form.action);
        }}
        // Also fix forms with empty or relative action
        if (!action || action === '' || action === '/login' || action.endsWith('/login')) {{
            form.action = PROXY + '/login';
            console.log('[PolySaaS] Fixed empty/relative form action to:', form.action);
        }}
    }});
}}

// Run form fix repeatedly as Vue mounts components dynamically
_fixLoginForms();
[100, 300, 500, 1000, 2000].forEach(function(ms) {{
    setTimeout(_fixLoginForms, ms);
}});

// Also observe DOM changes for dynamically added forms
var _formObserver = new MutationObserver(function(mutations) {{
    _fixLoginForms();
}});
document.addEventListener('DOMContentLoaded', function() {{
    _formObserver.observe(document.body, {{ childList: true, subtree: true }});
    _fixLoginForms();
}});

function _toProxy(u){{
    if(!u||typeof u!=='string')return u;
    var ap=_absUpstreamToProxy(u);
    if(ap!==null)return ap;
    if(u.indexOf(BASE)===0)return PROXY+u.slice(BASE.length);
    if(u.startsWith(PROXY))return u;
    if(u.startsWith(O+'/')){{
        u=u.slice(O.length);
        if(!u.startsWith('/'))u='/'+u;
    }}else if(u.startsWith('http:')||u.startsWith('https:')){{
        return u;
    }}
    if(u.charAt(0)==='/'&&_isPS(u))return u;
    if(u.charAt(0)==='/'){{
        for(var i=0;i<NC_PATHS.length;i++){{
            var p=NC_PATHS[i];
            if(u.startsWith(p)||u===p.replace(/\\/$/,''))return PROXY+u;
        }}
    }}
    return u;
}}

function _ncPathLooksLikeLogin(pathname){{
    if(!pathname)return true;
    var p=(''+pathname).toLowerCase();
    return p.endsWith('/login')||p.indexOf('/index.php/login')!==-1;
}}

// Patch fetch — Vue may use fetch or axios; after POST /login the document URL can stay on /login
var _f=window.fetch;
window.fetch=function(input,init){{
    if(typeof input==='string')input=_toProxy(input);
    else if(typeof Request!=='undefined'&&input instanceof Request){{
        var n=_toProxy(input.url);if(n!==input.url)input=new Request(n,input);
    }}
    var _method='GET';
    var _reqUrl='';
    if(typeof input==='string'){{_reqUrl=input;_method=(init&&init.method)||'GET';}}
    else if(typeof Request!=='undefined'&&input instanceof Request){{_reqUrl=input.url||'';_method=input.method||'GET';}}
    return _f.call(this,input,init).then(function(resp){{
        try{{
            var _loginUrl=_reqUrl.indexOf('/login')!==-1||_reqUrl.indexOf('index.php/login')!==-1;
            if(!resp||_method.toUpperCase()!=='POST'||!_loginUrl)return resp;
            var finalU=resp.url||'';
            if(!finalU||finalU.indexOf(O)!==0)return resp;
            var pu=new URL(finalU);
            if(_ncPathLooksLikeLogin(pu.pathname))return resp;
            if(resp.redirected||resp.ok)window.location.assign(finalU);
        }}catch(e){{}}
        return resp;
    }});
}};

// Patch XHR — Nextcloud login often uses XMLHttpRequest; responseURL is set after redirect chain
var _xo=XMLHttpRequest.prototype.open;
var _xs=XMLHttpRequest.prototype.send;
XMLHttpRequest.prototype.open=function(){{
    var a=Array.prototype.slice.call(arguments);
    this._polyNcMethod=(a[0]||'GET').toString().toUpperCase();
    this._polyNcUrl=typeof a[1]==='string'?a[1]:'';
    a[1]=_toProxy(a[1]);
    return _xo.apply(this,a);
}};
XMLHttpRequest.prototype.send=function(){{
    var self=this;
    var onDone=function(){{
        try{{
            if(self._polyNcMethod!=='POST')return;
            var u=self._polyNcUrl||'';
            if(u.indexOf('/login')===-1&&u.indexOf('index.php/login')===-1)return;
            var st=self.status|0;
            if(st<200||st>=500)return;
            var ru=self.responseURL||'';
            if(!ru||ru.indexOf(O)!==0)return;
            var pu=new URL(ru);
            if(_ncPathLooksLikeLogin(pu.pathname))return;
            window.location.assign(ru);
        }}catch(e){{}}
    }};
    self.addEventListener('load',onDone);
    return _xs.apply(self,arguments);
}};

var _WS=WebSocket;
window.WebSocket=function(url,protocols){{
    if(typeof url==='string'){{
        try{{
            var u=new URL(url,location.href);
            u.hostname=location.hostname;
            u.port=location.port||'';
            u.protocol=(location.protocol==='https:')?'wss:':'ws:';
            if(!u.pathname.startsWith('/pt/'))u.pathname=PROXY+u.pathname;
            url=u.toString();
            console.log('[PolySaaS Nextcloud] WebSocket via proxy:',url);
        }}catch(e){{console.warn('[PolySaaS Nextcloud] WebSocket rewrite:',e);}}
    }}
    if(protocols!==undefined)return new _WS(url,protocols);
    return new _WS(url);
}};
if(_WS.CONNECTING!==undefined)window.WebSocket.CONNECTING=_WS.CONNECTING;
if(_WS.OPEN!==undefined)window.WebSocket.OPEN=_WS.OPEN;
if(_WS.CLOSING!==undefined)window.WebSocket.CLOSING=_WS.CLOSING;
if(_WS.CLOSED!==undefined)window.WebSocket.CLOSED=_WS.CLOSED;

function _patchProp(proto,prop){{
    var d=Object.getOwnPropertyDescriptor(proto,prop);
    if(!d||!d.set)return;
    Object.defineProperty(proto,prop,{{
        get:d.get,
        set:function(v){{if(typeof v==='string')v=_toProxy(v);d.set.call(this,v);}},
        configurable:true,enumerable:true
    }});
}}
_patchProp(HTMLScriptElement.prototype,'src');
_patchProp(HTMLLinkElement.prototype,'href');
_patchProp(HTMLImageElement.prototype,'src');
var _setAttr=Element.prototype.setAttribute;
Element.prototype.setAttribute=function(name,value){{
    if(typeof value==='string'){{
        var ln=name.toLowerCase();
        if((ln==='src'||ln==='href')&&
            (this instanceof HTMLScriptElement||this instanceof HTMLLinkElement||this instanceof HTMLImageElement))
            value=_toProxy(value);
    }}
    return _setAttr.call(this,name,value);
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

console.log('[PolySaaS Nextcloud] Full shim active, proxy='+PROXY);
}})();
</script>
"""

    # ------------------------------------------------------------------
    # Static asset handling stub (used by some middleware paths)
    # ------------------------------------------------------------------

    def handle_static_asset(self, request_path, ext_path_str):
        return None
