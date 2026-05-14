# Auto-generated PassthroughHandler for Mattermost
# Generated from PolySniffer analysis of http://localhost:8065
# 
# This handler provides:
# - SSO via get_upstream_cookies()
# - URL rewriting for static assets and API calls
# - Client-side shim for dynamic requests (fetch, XHR, WebSocket)
# - Strict enforcement of /pt/admin/mattermost/ prefix

import json
import logging
import re
import time
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class MattermostPassthroughHandler:
    """
    Passthrough handler for Mattermost.
    Generated from PolySniffer captures - do not hand-edit.
    Regenerate from fresh captures if behavior changes.
    """

    def should_delegate_pt_admin_core(self, request, path_info: str) -> bool:
        """Static bundle URLs are served by mattermost_static_proxy in URLconf, not PT core."""
        import re as _re
        m = _re.match(r'^/pt/admin/([^/]+)/static/', path_info)
        return bool(m and 'mattermost' in m.group(1).lower())

    def try_root_display_shell_response(self, request, endpoint, url_trigger_segment):
        """
        Root-only intercept:
          - Token present → forward to Mattermost (return None).
          - No token     → try server-side SSO; if that works set cookie + redirect
                           to /channels/town-square; otherwise serve login bridge
                           INLINE (no redirect to /login — that caused the loop).
        All non-root paths return None immediately so the forwarder handles them.
        """
        if request.method != "GET":
            return None
        trigger = url_trigger_segment.strip("/")
        proxy_prefix = f"/pt/admin/{trigger}"

        # Only intercept the exact root. Everything else (channels, api, login, …)
        # is forwarded to Mattermost directly — no /login intercept here.
        if request.path_info.rstrip("/") != proxy_prefix:
            return None

        # Check for force=1 parameter to skip token validation (used when shim detects invalid token)
        force_login = request.GET.get('force') == '1'
        
        token = request.COOKIES.get('MMAUTHTOKEN') or request.COOKIES.get('mmauthtoken')
        if token and not force_login:
            print(f"[MM] MMAUTHTOKEN present — validating before redirect...")
            # Validate the browser token before redirecting
            import requests as _req
            try:
                _ep = getattr(request, '_passthrough_endpoint', None)
                _ep_url = getattr(_ep, 'endpoint_url', None) or 'https://polysaas-mattermost.onrender.com'
                _verify = _req.get(
                    f'{_ep_url}/api/v4/users/me',
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=5,
                )
                if _verify.status_code == 200:
                    print(f"[MM] Browser token valid — redirecting to /channels/town-square")
                    from django.http import HttpResponseRedirect
                    return HttpResponseRedirect(f"{proxy_prefix}/channels/town-square")
                else:
                    print(f"[MM] Browser token invalid ({_verify.status_code}) — clearing and showing login bridge")
                    # Clear the invalid token from cache
                    try:
                        extra_config = self._get_tenantapp_extra_config(request)
                        if extra_config:
                            for key in ['mmauthtoken', 'mm_session_token', 'mm_token', 'mmauthtoken_time', 'mm_session_token_time']:
                                if key in extra_config:
                                    del extra_config[key]
                            self._save_tenantapp_config(request, extra_config)
                    except Exception:
                        pass
            except Exception as exc:
                print(f"[MM] Token validation failed: {exc} — showing login bridge")

        # No browser token — try a quick server-side SSO first.
        from django.http import HttpResponseRedirect
        sso_token = None
        try:
            cookies = self.get_upstream_cookies(request) or {}
            sso_token = cookies.get('MMAUTHTOKEN')
        except Exception as exc:
            print(f"[MM SSO] get_upstream_cookies failed: {exc}")

        if sso_token:
            print(f"[MM SSO] Server-side token obtained ({sso_token[:8]}...) — cookie + redirect")
            resp = HttpResponseRedirect(f"{proxy_prefix}/channels/town-square")
            resp.set_cookie(
                'MMAUTHTOKEN', sso_token,
                max_age=86400, path='/', samesite='Lax',
                secure=request.is_secure(), httponly=False,
            )
            return resp

        # No server token — serve the login bridge INLINE (avoids redirect loop).
        print(f"[MM SSO] No token — serving login bridge inline at root")
        return self._serve_login_bridge(request, trigger, endpoint)

    def _serve_login_bridge(self, request, trigger, endpoint):
        """Plain HTML login bridge. No React, no frameworks. Just a form + XHR."""
        from django.http import HttpResponse
        from html import escape as h

        login_id = ""
        password = ""
        try:
            extra = self._get_tenantapp_extra_config(request) or {}
            login_id = (extra.get('mattermost_login_id') or extra.get('mm_login_id') or
                        extra.get('login_id') or
                        getattr(getattr(request, 'user', None), 'email', '') or '')
            password = (extra.get('mattermost_password') or extra.get('mm_password') or
                        extra.get('password') or '')
        except Exception as exc:
            logger.warning("[MM LoginBridge] Credentials lookup failed: %s", exc)

        logger.info("[MM LoginBridge] login_id=%r len=%d password_present=%s",
                    login_id, len(login_id or ''), bool(password))

        # HTML-escape so a quote in the password can't break the value attribute.
        lid_attr = h(login_id, quote=True)
        pwd_attr = h(password, quote=True)

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Sign in · Mattermost</title>
<style>
.mm-bridge {{ font-family: system-ui, sans-serif; padding: 40px 20px;
              display: flex; justify-content: center; }}
.mm-bridge .card {{ background: #fff; padding: 32px; border-radius: 10px; width: 380px;
                    box-shadow: 0 4px 20px rgba(0,0,0,.12); border: 1px solid #e5e7eb; }}
.mm-bridge h2 {{ margin: 0 0 6px 0; color: #1e325c; font-size: 20px; }}
.mm-bridge .sub {{ color: #666; font-size: 13px; margin-bottom: 18px; }}
.mm-bridge input {{ width: 100%; padding: 11px; margin: 6px 0; border: 1px solid #ccc;
                    border-radius: 5px; font-size: 14px; box-sizing: border-box; }}
.mm-bridge button {{ width: 100%; padding: 12px; background: #1e74d4; color: #fff; border: 0;
                     border-radius: 5px; font-size: 15px; font-weight: 600; cursor: pointer;
                     margin-top: 14px; }}
.mm-bridge button:hover {{ background: #1660b8; }}
.mm-bridge button:disabled {{ background: #888; cursor: not-allowed; }}
.mm-bridge #status {{ margin-top: 12px; text-align: center; font-size: 13px; min-height: 18px; color: #666; }}
.mm-bridge #status.err {{ color: #b91c1c; }}
</style></head>
<body>
<div class="mm-bridge">
<div class="card">
  <h2>Sign in to Mattermost</h2>
  <div class="sub">via PolySaaS Passthrough</div>
  <input type="text" id="lid" placeholder="Email or Username" value="{lid_attr}" autocomplete="username">
  <input type="password" id="pwd" placeholder="Password" value="{pwd_attr}" autocomplete="current-password">
  <button id="btn" type="button">Sign In</button>
  <div id="status"></div>
</div>
<script>
(function () {{
    function $(id) {{ return document.getElementById(id); }}
    function setStatus(msg, err) {{
        var s = $('status');
        s.className = err ? 'err' : '';
        s.textContent = msg;
    }}
    function base() {{
        return window.location.pathname.replace(/\/login(\/.*)?$/, '') || '/';
    }}
    function doLogin() {{
        var lid = $('lid').value.trim();
        var pwd = $('pwd').value;
        if (!lid || !pwd) {{ setStatus('Enter username and password.', true); return; }}
        $('btn').disabled = true;
        setStatus('Signing in...');

        var url = base().replace(/\/$/, '') + '/api/v4/users/login';
        console.log('[LoginBridge] POST', url);

        var xhr = new XMLHttpRequest();
        xhr.open('POST', url, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.withCredentials = true;
        xhr.onload = function () {{
            var token = xhr.getResponseHeader('Token');
            console.log('[LoginBridge] status=' + xhr.status + ' token=' + (token ? 'yes' : 'no') +
                        ' body=' + (xhr.responseText || '').slice(0, 300));
            if (xhr.status >= 200 && xhr.status < 300 && token) {{
                try {{ localStorage.setItem('MMAUTHTOKEN', token); }} catch (e) {{}}
                try {{ localStorage.setItem('storage:MMAUTHTOKEN', JSON.stringify(token)); }} catch (e) {{}}
                document.cookie = 'MMAUTHTOKEN=' + token + '; path=/; max-age=86400; SameSite=Lax';
                setStatus('Success! Loading...');
                window.location.replace(base() + '/channels/town-square');
                return;
            }}
            var msg = 'Login failed (HTTP ' + xhr.status + ')';
            try {{ var b = JSON.parse(xhr.responseText || '{{}}'); if (b.message) msg = b.message; }} catch (e) {{}}
            $('btn').disabled = false;
            setStatus(msg, true);
        }};
        xhr.onerror = function () {{
            $('btn').disabled = false;
            setStatus('Network error.', true);
        }};
        xhr.send(JSON.stringify({{ login_id: lid, password: pwd }}));
    }}

    document.addEventListener('DOMContentLoaded', function () {{
        $('btn').addEventListener('click', doLogin);
        console.log('[LoginBridge] loaded. lid=' + ($('lid').value ? 'yes' : 'no') +
                    ' pwd=' + ($('pwd').value ? 'yes' : 'no'));
        if ($('lid').value && $('pwd').value) {{
            setTimeout(doLogin, 300);
        }}
    }});
}})();
</script>
</div>
</body></html>"""

        resp = HttpResponse(html, content_type="text/html; charset=utf-8")
        resp["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return resp

    def process_html_response(self, html_str, request, endpoint_url=None, *args, **kwargs):
        print(f"[MattermostPassthroughHandler] process_html_response called, path={request.path_info}, html_len={len(html_str)}")

        # If Mattermost served its login HTML, replace entirely with our own form.
        if '/login' in (getattr(request, 'path_info', '') or ''):
            _path_parts = (getattr(request, 'path_info', '') or '').strip('/').split('/')
            if len(_path_parts) >= 3 and _path_parts[0] == 'pt' and _path_parts[1] == 'admin':
                _proxy_prefix = f"/pt/admin/{_path_parts[2]}"
            else:
                _proxy_prefix = "/pt/admin/mattermost"
            _trigger = _path_parts[2] if len(_path_parts) >= 3 else "mattermost"
            _endpoint_stub = type('E', (), {'endpoint_url': f"https://{_trigger}"})()
            bridge = self._serve_login_bridge(request, _trigger, _endpoint_stub)
            if bridge is not None:
                return bridge

        if not endpoint_url:
            return html_str, None

        origin = endpoint_url.rstrip("/")
        parsed = urlparse(origin)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"
        # Derive proxy_prefix from the request path — never hardcode.
        _path_parts = request.path_info.strip('/').split('/')
        if len(_path_parts) >= 3 and _path_parts[0] == 'pt' and _path_parts[1] == 'admin':
            proxy_prefix = f"/pt/admin/{_path_parts[2]}"
        else:
            proxy_prefix = "/pt/admin/mattermost"

        html_str = self._strip_base_tags(html_str)
        html_str = self._strip_meta_redirects(html_str)
        html_str = self._strip_csp(html_str)

        # Rewrite form action attributes so native form POSTs go through the proxy prefix.
        html_str = re.sub(
            r'(action=)(["\'])(/[^"\']*)',
            lambda m: f'{m.group(1)}{m.group(2)}{proxy_prefix}{m.group(3)}{m.group(2)}',
            html_str,
            flags=re.IGNORECASE,
        )

        # Rewrite file paths with extensions (capture query param as part of group 3, not separate)
        html_str = re.sub(
            r'(src|href)=(["\'])([^"\']*?[\w.-]+\.(js|css|png|jpg|jpeg|gif|svg|woff2?|ttf|eot|json|map)(?:\?[^"\']*)?)',
            lambda m: f'{m.group(1)}={m.group(2)}{proxy_prefix}{m.group(3)}{m.group(2)}',
            html_str,
            flags=re.IGNORECASE,
        )

        html_str = re.sub(
            r'(src|href)=(["\'])(/static/[^"\']*(?:\?[^"\']*)?)',
            lambda m: f'{m.group(1)}={m.group(2)}{proxy_prefix}{m.group(3)}{m.group(2)}',
            html_str,
            flags=re.IGNORECASE,
        )

        # Rewrite absolute upstream-origin URLs (e.g. https://polysaas-mattermost.onrender.com/static/...)
        _abs_static = re.escape(base_origin) + r'/static/'
        html_str = re.sub(
            r'(src|href)=(["\'])' + _abs_static + r'([^"\']*)',
            lambda m: f'{m.group(1)}={m.group(2)}{proxy_prefix}/static/{m.group(3)}{m.group(2)}',
            html_str,
            flags=re.IGNORECASE,
        )

        # Rewrite window.basename so React Router uses proxy prefix as its base
        html_str = re.sub(
            r"(window\.basename\s*=\s*)['\"][^'\"]*['\"]",
            lambda m: m.group(1) + f"'{proxy_prefix}'",
            html_str,
        )

        # Inject the full client shim into every proxied HTML page so the
        # auto-login watcher runs on /login regardless of navigation path.
        if '<head' in html_str.lower():
            print(f"[MM HANDLER] Injecting shim into HTML, proxy_prefix={proxy_prefix}")
            html_str = self._inject_client_shim(html_str, base_origin, request, proxy_prefix)
        else:
            print(f"[MM HANDLER] No <head> found, skipping shim injection")

        return html_str, None

    def rewrite_upstream_body(self, body, content_type, request, endpoint_url=None, upstream_path=None):
        """Rewrite SiteURL and WebsocketURL in Mattermost config/client response."""
        if not upstream_path or '/api/v4/config/client' not in upstream_path:
            return None
        if 'json' not in (content_type or '').lower():
            return None
        try:
            import json as _json
            data = _json.loads(body)
            scheme = 'https' if request.is_secure() else 'http'
            origin = f"{scheme}://{request.get_host()}"
            # Rewrite to origin-only — no proxy prefix. Mattermost's Client4 will call
            # http://localhost:8000/api/v4/... and the shim's toProxy() converts those
            # transparently to /pt/admin/mattermost/api/v4/... Mattermost never sees /pt/admin/.
            if 'SiteURL' in data:
                print(f"[MM] Rewriting SiteURL: {data['SiteURL']} -> {origin}")
                data['SiteURL'] = origin
            if 'WebsocketURL' in data:
                ws_scheme = 'wss' if request.is_secure() else 'ws'
                ws_origin = f"{ws_scheme}://{request.get_host()}"
                data['WebsocketURL'] = ws_origin
                print(f"[MM] Rewriting WebsocketURL -> {ws_origin}")
            return _json.dumps(data).encode('utf-8')
        except Exception as exc:
            print(f"[MM] rewrite_upstream_body failed: {exc}")
            return None

    def _get_tenantapp_extra_config(self, request=None):
        """Query TenantApp extra_config from public schema using raw SQL to avoid schema issues.
        Filters by current tenant first; falls back to any active mattermost TenantApp."""
        import json
        from django.db import connection
        tenant_id = None
        if request is not None:
            try:
                from dose.utils import get_current_tenant
                t = getattr(request, 'tenant', None) or get_current_tenant(request)
                if t:
                    tenant_id = t.id
            except Exception:
                pass
        with connection.cursor() as cur:
            cur.execute("SET search_path TO public,pg_catalog")
            # Try tenant-specific record first (any status with non-empty config)
            if tenant_id:
                cur.execute(
                    """SELECT extra_config FROM dose_tenantapp
                       WHERE app_name = 'mattermost' AND tenant_id = %s
                       AND extra_config IS NOT NULL AND extra_config != '{}'::jsonb
                       LIMIT 1""",
                    [tenant_id],
                )
                row = cur.fetchone()
                if row and row[0]:
                    cfg = row[0]
                    if isinstance(cfg, str):
                        return json.loads(cfg)
                    return cfg
            # Fall back to any active mattermost TenantApp with credentials
            cur.execute(
                """SELECT extra_config FROM dose_tenantapp
                   WHERE app_name = 'mattermost' AND status = 'active'
                   AND extra_config IS NOT NULL AND extra_config != '{}'::jsonb
                   LIMIT 1""",
            )
            row = cur.fetchone()
            if row and row[0]:
                cfg = row[0]
                if isinstance(cfg, str):
                    return json.loads(cfg)
                return cfg
        return None

    def _save_tenantapp_token(self, token, request=None):
        """Save refreshed token to public schema TenantApp using raw SQL."""
        import json
        import time
        from django.db import connection
        tenant_id = None
        if request is not None:
            try:
                from dose.utils import get_current_tenant
                t = getattr(request, 'tenant', None) or get_current_tenant(request)
                if t:
                    tenant_id = t.id
            except Exception:
                pass
        with connection.cursor() as cur:
            cur.execute("SET search_path TO public,pg_catalog")
            extra = self._get_tenantapp_extra_config(request) or {}
            extra['mmauthtoken'] = token
            extra['mmauthtoken_time'] = time.time()
            extra['mm_session_token'] = token
            extra['mm_session_token_time'] = time.time()
            if tenant_id:
                cur.execute(
                    """UPDATE dose_tenantapp SET extra_config = %s
                       WHERE app_name = 'mattermost' AND tenant_id = %s""",
                    [json.dumps(extra), tenant_id],
                )
            else:
                cur.execute(
                    """UPDATE dose_tenantapp SET extra_config = %s
                       WHERE app_name = 'mattermost' AND status = 'active'""",
                    [json.dumps(extra)],
                )

    def _save_tenantapp_config(self, request, extra_config: dict):
        """Save extra_config to TenantApp without modifying token fields."""
        import json
        from django.db import connection
        tenant_id = None
        if request is not None:
            try:
                from dose.utils import get_current_tenant
                t = getattr(request, 'tenant', None) or get_current_tenant(request)
                if t:
                    tenant_id = t.id
            except Exception:
                pass
        with connection.cursor() as cur:
            cur.execute("SET search_path TO public,pg_catalog")
            if tenant_id:
                cur.execute(
                    """UPDATE dose_tenantapp SET extra_config = %s
                       WHERE app_name = 'mattermost' AND tenant_id = %s""",
                    [json.dumps(extra_config), tenant_id],
                )
            else:
                cur.execute(
                    """UPDATE dose_tenantapp SET extra_config = %s
                       WHERE app_name = 'mattermost' AND status = 'active'""",
                    [json.dumps(extra_config)],
                )

    def filter_cookies_for_upstream(self, request, cookies: dict) -> dict:
        """Strip MMAUTHTOKEN on login/logout requests so a stale session can't poison auth."""
        path = (getattr(request, 'path_info', '') or '')
        if '/api/v4/users/login' in path or '/api/v4/users/logout' in path:
            cookies = {k: v for k, v in (cookies or {}).items()
                       if k.lower() not in ('mmauthtoken',)}
        return cookies

    def get_upstream_cookies(self, request):
        """
        Provide session cookies for SSO/auto-login to Mattermost.
        Mattermost primarily uses MMAUTHTOKEN header/cookie.
        """
        # Don't inject a session token into the login/logout request itself —
        # Mattermost rejects login attempts that carry a stale session.
        _path = (getattr(request, 'path_info', '') or '')
        if '/api/v4/users/login' in _path or '/api/v4/users/logout' in _path:
            return {}
        try:
            from dose.utils import get_current_tenant
            import requests as _req

            tenant = get_current_tenant(request)
            print(f"[MM_AUTH] tenant: {tenant}")
            if not tenant:
                return {}

            extra_config = self._get_tenantapp_extra_config(request)
            print(f"[MM_AUTH] extra_config found: {extra_config is not None}")

            if not extra_config:
                print("[MM_AUTH] No extra_config for mattermost TenantApp")
                return {}

            # Try cached MMAUTHTOKEN first
            token = (extra_config.get('mmauthtoken') or 
                     extra_config.get('mm_session_token') or
                     extra_config.get('mm_token'))
            token_time = (extra_config.get('mmauthtoken_time') or 
                          extra_config.get('mm_session_token_time', 0))

            if token and (time.time() - token_time < 3600):
                # Verify cached token is still valid before returning it
                _ep = getattr(request, '_passthrough_endpoint', None)
                _ep_url = getattr(_ep, 'endpoint_url', None) or ''
                _mm_origin_verify = (
                    extra_config.get('mm_url') or extra_config.get('mattermost_url') or _ep_url
                ).rstrip('/')
                try:
                    _verify = _req.get(
                        f'{_mm_origin_verify}/api/v4/users/me',
                        headers={'Authorization': f'Bearer {token}'},
                        timeout=5,
                    )
                    if _verify.status_code == 200:
                        logger.info("[MattermostPassthroughHandler] Cached token valid: %s...", token[:8])
                        return {'MMAUTHTOKEN': token}
                    print(f"[MM_AUTH] Cached token invalid ({_verify.status_code}), refreshing...")
                except Exception as _ve:
                    print(f"[MM_AUTH] Token verify error: {_ve}, refreshing...")

            # Refresh session if needed
            password = (extra_config.get('mattermost_password') or 
                        extra_config.get('mm_password') or
                        extra_config.get('password'))
            print(f"[MM_AUTH] password present: {bool(password)}")
            if not password:
                logger.warning("[MattermostPassthroughHandler] No password available in extra_config")
                return {}

            login_id = (extra_config.get('mattermost_login_id') or 
                        extra_config.get('mm_login_id') or
                        request.user.email)
            print(f"[MM_AUTH] login_id: {login_id}")

            _ep = getattr(request, '_passthrough_endpoint', None)
            _ep_url = getattr(_ep, 'endpoint_url', None) or ''
            mm_origin = (
                extra_config.get('mm_url') or
                extra_config.get('mattermost_url') or
                extra_config.get('mm_origin') or
                _ep_url
            ).rstrip('/')
            print(f"[MM_AUTH] mm_origin: {mm_origin}")
            resp = _req.post(
                f'{mm_origin}/api/v4/users/login',
                json={'login_id': login_id, 'password': password},
                timeout=10,
            )
            print(f"[MM_AUTH] login response status: {resp.status_code}")

            if resp.status_code == 200:
                token = resp.headers.get('Token')
                print(f"[MM_AUTH] Token header present: {bool(token)}")
                if token:
                    self._save_tenantapp_token(token, request)
                    logger.info("[MattermostPassthroughHandler] MMAUTHTOKEN refreshed: %s...", token[:8])
                    return {'MMAUTHTOKEN': token}

        except Exception as exc:
            logger.warning("[MattermostPassthroughHandler] get_upstream_cookies failed: %s", exc)
            print(f"[MM_AUTH] EXCEPTION: {exc}")

        return {}

    def augment_outbound_headers(self, request, headers: dict, target_url: str) -> None:
        """Inject Authorization Bearer token for all Mattermost requests forwarded through proxy."""
        print(f'[MM_AUTH] augment_outbound_headers called for {target_url}')
        # Never inject on login/logout — Mattermost rejects requests with a stale session token.
        if '/api/v4/users/login' in (target_url or '') or '/api/v4/users/logout' in (target_url or ''):
            print('[MM_AUTH] Skipping login/logout path')
            return
        
        # PRIORITY: Use server-cached token from TenantApp (verified and fresh)
        # Browser cookie from request.COOKIES may be stale or from a different session
        token = None
        _src = 'none'
        try:
            extra_config = self._get_tenantapp_extra_config(request)
            if extra_config:
                token = (extra_config.get('mmauthtoken') or
                         extra_config.get('mm_session_token') or
                         extra_config.get('mm_token'))
                if token:
                    _src = 'server-cache'
        except Exception as exc:
            print(f'[MM_AUTH] Error getting cached token: {exc}')
        
        # Fallback to browser cookie only if no server token available
        if not token:
            token = request.COOKIES.get('MMAUTHTOKEN') or request.COOKIES.get('mmauthtoken')
            if token:
                _src = 'browser-cookie'
        
        if token and 'Authorization' not in headers:
            headers['Authorization'] = f'Bearer {token}'
            print(f'[MM_AUTH] Injected Authorization ({_src}, token={token[:8]}...) for {target_url}')
        elif not token:
            print(f'[MM_AUTH] NO TOKEN AVAILABLE for {target_url} — request will be unauthenticated')

    def postprocess_upstream_response(self, resp, request, **kwargs):
        """Hook to handle upstream responses - clear token on 401 to break redirect loops."""
        target_url = kwargs.get('endpoint_url', '')
        # If we get a 401 on /api/v4/users/me, the cached token is invalid
        if resp.status_code == 401 and '/api/v4/users/me' in (target_url or ''):
            print(f'[MM_AUTH] Got 401 on /api/v4/users/me - clearing invalid cached token')
            try:
                extra_config = self._get_tenantapp_extra_config(request)
                if extra_config:
                    # Clear all token fields
                    for key in ['mmauthtoken', 'mm_session_token', 'mm_token', 'mmauthtoken_time', 'mm_session_token_time']:
                        if key in extra_config:
                            del extra_config[key]
                    self._save_tenantapp_config(request, extra_config)
                    print(f'[MM_AUTH] Cleared invalid token from cache')
            except Exception as exc:
                print(f'[MM_AUTH] Failed to clear token: {exc}')
        return None  # Return None to let normal processing continue

    def _strip_base_tags(self, html):
        return re.sub(r"<base\b[^>]*>", "", html, flags=re.IGNORECASE)

    def _strip_meta_redirects(self, html):
        return re.sub(r'<meta\s+http-equiv\s*=\s*["\']refresh["\'][^>]*>', "", html, flags=re.IGNORECASE)

    def _strip_csp(self, html):
        return re.sub(r'<meta\s+http-equiv\s*=\s*["\']Content-Security-Policy["\'][^>]*>', "", html, flags=re.IGNORECASE)

    def _mattermost_display_shim_html(
        self, request, proxy_prefix: str, base_origin: str
    ) -> str:
        """
        Full client shim for Mattermost in PolySaaS: MMAUTHTOKEN, webpack public path,
        fetch/XHR/WebSocket → proxy, attribute/prototype patching (matches generated handler).
        Display shell must include network patches or API/WS stay on the admin origin → spinner.
        """
        # Use the server's verified token (from get_upstream_cookies which validates it).
        # Browser may have a stale/invalid token from a previous session - always trust server.
        token = ""
        try:
            cookies = self.get_upstream_cookies(request) or {}
            token = cookies.get("MMAUTHTOKEN") or ""
        except Exception as exc:
            logger.warning("[MattermostPassthroughHandler] Token lookup failed: %s", exc)
        # Fallback to browser cookie only if server has no valid token
        if not token:
            token = request.COOKIES.get('MMAUTHTOKEN') or request.COOKIES.get('mmauthtoken') or ""
        logger.info("[MM Shim] token source=%s len=%d",
                    'server' if token else 'none', len(token))

        login_id = ""
        password = ""
        try:
            extra = self._get_tenantapp_extra_config(request) or {}
            login_id = (extra.get('mattermost_login_id') or
                        extra.get('login_id') or
                        getattr(getattr(request, 'user', None), 'email', '') or '')
            password = (extra.get('mattermost_password') or extra.get('password') or '')
        except Exception as exc:
            logger.warning("[MattermostPassthroughHandler] Credentials lookup failed: %s", exc)

        token_js = json.dumps(token)
        login_id_js = json.dumps(login_id)
        password_js = json.dumps(password)
        proxy_js = json.dumps(proxy_prefix)
        base_js = json.dumps(base_origin.rstrip("/"))
        print(f"[MM SHIM INJECT] token_len={len(token)} token_preview={token[:20] if token else 'NONE'}")

        return f"""
<script data-polysaas-mattermost-shim="1">
(function() {{
    var B = {base_js};
    var PROXY = {proxy_js};
    var O = window.location.origin;
    var MMAUTHTOKEN = {token_js};
    var MM_LOGIN_ID = {login_id_js};
    var MM_PASSWORD = {password_js};

    // Spy on localStorage reads to diagnose what key Mattermost uses for the auth token
    var _lsGet = Storage.prototype.getItem;
    Storage.prototype.getItem = function(key) {{
        var val = _lsGet.call(this, key);
        if (key && (key.indexOf('MMAUTHTOKEN') !== -1 || key.indexOf('MMAuth') !== -1 ||
                    key.indexOf('persist:') !== -1 || key.indexOf('credentials') !== -1)) {{
            console.log('[PolySaaS MM] localStorage.getItem("' + key + '") =>', val ? val.slice(0, 60) : 'null');
        }}
        return val;
    }};
    var _lsSet = Storage.prototype.setItem;
    Storage.prototype.setItem = function(key, value) {{
        if (key && (key.indexOf('MMAUTHTOKEN') !== -1 || key.indexOf('MMAuth') !== -1 ||
                    key.indexOf('persist:') !== -1 || key.indexOf('credentials') !== -1)) {{
            var display = typeof value === 'string' ? value.slice(0, 60) : value;
            console.log('[PolySaaS MM] localStorage.setItem("' + key + '") =', display);
        }}
        return _lsSet.call(this, key, value);
    }};

    var PS_PREFIXES = ['/static/admin/', '/static/img/', '/admin/', '/dose/', '/media/', '/accounts/', '/pt/', '/favicon'];
    function isPolySaaSPath(s) {{
        for (var i = 0; i < PS_PREFIXES.length; i++) {{
            if (s.startsWith(PS_PREFIXES[i])) return true;
        }}
        return false;
    }}

    function toProxy(s) {{
        if (typeof s !== 'string') return s;
        if (!s || s.startsWith('data:') || s.startsWith('blob:')) return s;
        if (s.startsWith(B)) {{
            var tail = s.slice(B.length);
            if (!tail.startsWith('/')) tail = '/' + tail;
            return PROXY + tail;
        }}
        if (s.startsWith(O + '/')) s = s.slice(O.length);
        else if (s.startsWith('http:') || s.startsWith('https:') || s.indexOf('//') === 0) return s;
        if (s.charAt(0) !== '/') return s;
        if (isPolySaaSPath(s)) return s;
        return PROXY + s;
    }}

    // Cookie + localStorage fallback (server-side fetch interceptor still injects MM-Auth-Token header)
    if (MMAUTHTOKEN) {{
        // Clear any old/stale tokens first
        try {{ localStorage.removeItem('storage:MMAUTHTOKEN'); }} catch(_e) {{}}
        try {{ localStorage.removeItem('storage:MMAuthtokenExpiry'); }} catch(_e) {{}}
        try {{ localStorage.removeItem('MMAUTHTOKEN'); }} catch(_e) {{}}
        try {{
            localStorage.setItem('storage:MMAUTHTOKEN', JSON.stringify(MMAUTHTOKEN));
            localStorage.setItem('storage:MMAuthtokenExpiry', JSON.stringify(Date.now() + 108000000));
            localStorage.setItem('MMAUTHTOKEN', MMAUTHTOKEN);
        }} catch(_e) {{}}
        document.cookie = 'MMAUTHTOKEN=' + MMAUTHTOKEN + '; path=/; max-age=108000';
        window.MMAUTHTOKEN = MMAUTHTOKEN;
    }}

    console.log('[PolySaaS MM] Shim loaded. token preview:', MMAUTHTOKEN ? MMAUTHTOKEN.substring(0, 8) + '...' : 'none');

    // Intercept client-side React Router navigation to /login.
    // Mattermost SPA pushes /login when its token check fails; without this hook
    // the URL changes but no server GET fires, so our bridge never serves.
    // Forcing window.location.replace produces a real GET that hits our bridge.
    (function() {{
        var _push = history.pushState;
        var _repl = history.replaceState;
        function isLoginPath(url) {{
            try {{
                var p = (typeof url === 'string') ? url : (url && url.pathname) || '';
                return /\/login(\/.*)?$/.test(p);
            }} catch (e) {{ return false; }}
        }}
        history.pushState = function(state, title, url) {{
            if (isLoginPath(url)) {{
                console.log('[PolySaaS MM] Intercept pushState(/login) -> hard redirect to bridge');
                window.location.replace(PROXY + '/login');
                return;
            }}
            return _push.apply(this, arguments);
        }};
        history.replaceState = function(state, title, url) {{
            if (isLoginPath(url)) {{
                console.log('[PolySaaS MM] Intercept replaceState(/login) -> hard redirect to bridge');
                window.location.replace(PROXY + '/login');
                return;
            }}
            return _repl.apply(this, arguments);
        }};
    }})();

    window.__webpack_public_path__ = PROXY + '/static/';
    window.basename = PROXY;

    // Strip PolySaaS proxy paths from redirect_to — Mattermost history.push(redirect_to)
    // would navigate within the SPA and fail to match any route, falling back to /login.
    try {{
        var _rurl = new URL(window.location.href);
        var _rt = _rurl.searchParams.get('redirect_to');
        if (_rt && (_rt.startsWith('/pt/') || _rt.indexOf('://') !== -1)) {{
            _rurl.searchParams.delete('redirect_to');
            window.history.replaceState({{}}, '', _rurl.toString());
            console.log('[PolySaaS MM] Stripped invalid redirect_to:', _rt);
        }}
    }} catch(e) {{}}

    var _f = window.fetch;
    window.fetch = function(input, init) {{
        var original = input;
        if (typeof input === 'string') {{
            input = toProxy(input);
        }} else if (typeof Request !== 'undefined' && input instanceof Request) {{
            var u = toProxy(input.url);
            if (u !== input.url) input = new Request(u, input);
        }}
        if (MMAUTHTOKEN) {{
            var reqUrl = typeof input === 'string' ? input : (input && input.url ? input.url : '');
            if (reqUrl.indexOf('/api/v4/') !== -1) {{
                init = Object.assign({{}}, init || {{}});
                if (!init.headers) {{
                    init.headers = {{'Authorization': 'Bearer ' + MMAUTHTOKEN}};
                }} else if (typeof init.headers.has === 'function') {{
                    init.headers.set('Authorization', 'Bearer ' + MMAUTHTOKEN);
                }} else {{
                    init.headers = Object.assign({{}}, init.headers, {{'Authorization': 'Bearer ' + MMAUTHTOKEN}});
                }}
                console.log('[PolySaaS MM] Auth injected for', reqUrl.slice(0, 60));
            }}
        }}
        if (original !== input) console.log('[PolySaaS MM] fetch:', original, '->', input);
        var _reqUrlForLog = typeof input === 'string' ? input : (input && input.url ? input.url : '');
        var _prom = _f.call(this, input, init);
        if (_reqUrlForLog.indexOf('/users/me') !== -1) {{
            return _prom.then(function(r) {{
                console.log('[PolySaaS MM] users/me HTTP status:', r.status, r.ok ? 'OK' : 'FAIL');
                // If we get 401, the token is invalid - clear it and redirect to login
                if (r.status === 401) {{
                    console.log('[PolySaaS MM] Token invalid (401) - clearing and redirecting to login');
                    try {{ localStorage.removeItem('storage:MMAUTHTOKEN'); }} catch(_e) {{}}
                    try {{ localStorage.removeItem('storage:MMAuthtokenExpiry'); }} catch(_e) {{}}
                    try {{ localStorage.removeItem('MMAUTHTOKEN'); }} catch(_e) {{}}
                    document.cookie = 'MMAUTHTOKEN=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
                    // Redirect to login bridge after a short delay
                    setTimeout(function() {{
                        window.location.replace(PROXY + '/login?force=1');
                    }}, 500);
                }}
                return r;
            }});
        }}
        return _prom;
    }};

    var _xo = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {{
        var proxied = toProxy(url);
        if (url !== proxied) console.log('[PolySaaS MM] XHR:', method, url, '->', proxied);
        var rest = Array.prototype.slice.call(arguments, 2);
        _xo.apply(this, [method, proxied].concat(rest));
        if (proxied.indexOf('/users/me') !== -1) {{
            var _self = this;
            this.addEventListener('load', function() {{
                console.log('[PolySaaS MM] XHR users/me status:', _self.status);
            }});
        }}
        if (MMAUTHTOKEN && proxied.indexOf('/api/v4/') !== -1) {{
            try {{
                this.setRequestHeader('Authorization', 'Bearer ' + MMAUTHTOKEN);
                if (proxied.indexOf('/users/me') !== -1)
                    console.log('[PolySaaS MM] XHR Auth injected for users/me, token starts:', MMAUTHTOKEN.slice(0, 8));
            }} catch(e) {{}}
        }}
    }};

    var _WS = WebSocket;
    window.WebSocket = function(url, protocols) {{
        if (typeof url === 'string') {{
            try {{
                // Route WebSocket DIRECTLY to the Mattermost server — never through the
                // WSGI proxy (which cannot handle protocol upgrades and causes the
                // "Mattermost unreachable" red banner).
                var mmOrigin = new URL(B);
                var u = new URL(url, location.href);
                u.hostname = mmOrigin.hostname;
                u.port = mmOrigin.port || '';
                u.protocol = 'wss:';
                // Keep the path as-is (e.g. /api/v4/websocket) — no PROXY prefix.
                url = u.toString();
                console.log('[PolySaaS Mattermost] WebSocket direct to MM server:', url);
            }} catch (e) {{ console.warn('[PolySaaS Mattermost] WebSocket rewrite:', e); }}
        }}
        if (protocols !== undefined) return new _WS(url, protocols);
        return new _WS(url);
    }};
    if (_WS.CONNECTING !== undefined) window.WebSocket.CONNECTING = _WS.CONNECTING;
    if (_WS.OPEN !== undefined) window.WebSocket.OPEN = _WS.OPEN;
    if (_WS.CLOSING !== undefined) window.WebSocket.CLOSING = _WS.CLOSING;
    if (_WS.CLOSED !== undefined) window.WebSocket.CLOSED = _WS.CLOSED;

    function patchProp(proto, prop) {{
        var d = Object.getOwnPropertyDescriptor(proto, prop);
        if (!d || !d.set) return;
        Object.defineProperty(proto, prop, {{
            get: d.get,
            set: function(v) {{
                if (typeof v === 'string') v = toProxy(v);
                d.set.call(this, v);
            }},
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
                value = toProxy(value);
            }}
        }}
        return _setAttr.call(this, name, value);
    }};

    // Monitor script errors from Mattermost bundles
    window.addEventListener('error', function(e) {{
        console.error('[PolySaaS MM] Global error:', e.message, 'at', e.filename, ':', e.lineno);
    }});
    window.addEventListener('unhandledrejection', function(e) {{
        console.error('[PolySaaS MM] Unhandled promise rejection:', e.reason);
    }});
    // Log when scripts are loaded
    var _origAppend = HTMLHeadElement.prototype.appendChild;
    HTMLHeadElement.prototype.appendChild = function(node) {{
        if (node.tagName === 'SCRIPT') console.log('[PolySaaS MM] Script appended:', node.src || '(inline)');
        return _origAppend.call(this, node);
    }};
    console.log('[PolySaaS Mattermost] Full shim loaded, proxy=', PROXY);
}})();
</script>
"""

    def _inject_client_shim(self, html, base_origin, request, proxy_prefix):
        """Inject full Mattermost shim first in <head>."""
        shim = self._mattermost_display_shim_html(
            request, proxy_prefix, base_origin
        )

        if re.search(r"<head\b", html, re.IGNORECASE):
            return re.sub(
                r"(<head[^>]*>)",
                lambda m: m.group(1) + shim,
                html,
                count=1,
                flags=re.IGNORECASE,
            )
        return shim + html
