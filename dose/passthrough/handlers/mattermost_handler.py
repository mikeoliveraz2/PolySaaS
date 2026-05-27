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

    _cors_patched = False  # class-level flag: only patch once per process

    def _ensure_cors_allowed(self, request, mm_origin, token):
        """Patch Mattermost's AllowCorsFrom once per process so WebSocket connections succeed."""
        if MattermostPassthroughHandler._cors_patched:
            return
        try:
            import requests as _req
            polysaas_origin = f"https://{request.get_host()}"
            # Get current config
            cfg_resp = _req.get(
                f'{mm_origin}/api/v4/config',
                headers={'Authorization': f'Bearer {token}'},
                timeout=10,
            )
            if cfg_resp.status_code != 200:
                print(f"[MM CORS] Cannot fetch config: {cfg_resp.status_code}")
                return
            cfg = cfg_resp.json()
            current = cfg.get('ServiceSettings', {}).get('AllowCorsFrom', '') or ''
            if polysaas_origin in current:
                print(f"[MM CORS] Already allowed: {current}")
                MattermostPassthroughHandler._cors_patched = True
                return
            new_val = f"{current},{polysaas_origin}" if current else polysaas_origin
            patch = {'ServiceSettings': {'AllowCorsFrom': new_val}}
            patch_resp = _req.put(
                f'{mm_origin}/api/v4/config/patch',
                json=patch,
                headers={'Authorization': f'Bearer {token}'},
                timeout=10,
            )
            if patch_resp.status_code == 200:
                print(f"[MM CORS] Patched AllowCorsFrom -> {new_val}")
                MattermostPassthroughHandler._cors_patched = True
            else:
                print(f"[MM CORS] Patch failed: {patch_resp.status_code} {patch_resp.text[:200]}")
        except Exception as exc:
            print(f"[MM CORS] Error: {exc}")

    def try_root_display_shell_response(self, request, endpoint, url_trigger_segment):
        """
        Root-only intercept:
          - Token present → forward to Mattermost (return None).
          - No token     → try server-side SSO; if that works set cookie + redirect
                           to /{team}/channels/town-square; otherwise serve login bridge
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

        # Let Mattermost handle team selection - don't specify team in redirect
        team_redirect = f"{proxy_prefix}/channels/town-square"
        print(f"[MM ROOT] redirect_target={team_redirect}")

        # Check for force=1 parameter to skip token validation (used when shim detects invalid token)
        force_login = request.GET.get('force') == '1'
        
        token = request.COOKIES.get('MMAUTHTOKEN') or request.COOKIES.get('mmauthtoken')
        if token and not force_login:
            # TRUST the browser cookie — don't validate server-side.
            # Server-side validation creates new sessions that invalidate the browser token.
            print(f"[MM ROOT] MMAUTHTOKEN present len={len(token)} — redirecting without validation")
            from django.http import HttpResponseRedirect
            resp = HttpResponseRedirect(team_redirect)
            resp.set_cookie(
                'MMAUTHTOKEN', token,
                max_age=86400, path='/', samesite='Lax',
                secure=request.is_secure(), httponly=False,
            )
            return resp

        # No browser token — serve the login bridge INLINE (avoids redirect loop).
        print(f"[MM ROOT] No browser token — serving login bridge inline at root")
        bridge = self._serve_login_bridge(request, trigger, endpoint)
        from dose.passthrough.forwarding import _wrap_in_admin_template
        return _wrap_in_admin_template(request, bridge, trigger, endpoint)

    def _serve_login_bridge(self, request, trigger, endpoint):
        """Plain HTML login bridge. No React, no frameworks. Just a form + XHR."""
        from django.http import HttpResponse
        from html import escape as h
        from dose.passthrough.credential_container import PassthroughCredentialContainer

        user_email = getattr(getattr(request, 'user', None), 'email', '') or ''
        login_id = ""
        password = ""
        allow_auto_submit = False
        try:
            # First try to get credentials from encrypted session storage
            session_creds = PassthroughCredentialContainer.retrieve(request, app_name='mattermost')
            if session_creds:
                candidate_login = session_creds.get('username', '')
                candidate_password = session_creds.get('password', '')
                if self._credential_matches_active_user(request, candidate_login):
                    login_id = candidate_login
                    password = candidate_password
                    allow_auto_submit = bool(login_id and password)
                    logger.info("[MM LoginBridge] Using active-user credentials from encrypted session")
                else:
                    logger.info("[MM LoginBridge] Ignoring session credentials that do not match the active user")

            # Fallback to extra_config if session credentials not available
            if not login_id or not password:
                extra = self._get_tenantapp_extra_config(request) or {}
                print(f"[MM LoginBridge] extra keys={list(extra.keys())}")
                stored_login = (extra.get('mattermost_username') or
                               extra.get('mattermost_login_id') or extra.get('mm_login_id') or
                               extra.get('username') or extra.get('login_id') or '')
                stored_pass = (extra.get('mattermost_password') or extra.get('mm_password') or
                              extra.get('password') or '')
                # Use stored credentials directly — they were provisioned for this tenant.
                # Fall back to Django username, then email if nothing stored.
                django_username = getattr(getattr(request, 'user', None), 'username', '') or ''
                login_id = stored_login or django_username or user_email
                password = stored_pass
        except Exception as exc:
            logger.warning("[MM LoginBridge] Credentials lookup failed: %s", exc)
            login_id = user_email

        print(f"[MM LoginBridge] login_id={login_id!r} password_present={bool(password)} user_email={user_email!r}")

        # HTML-escape so a quote in the password can't break the value attribute.
        lid_attr = h(login_id, quote=True)
        pwd_attr = h(password, quote=True)
        user_email_js = json.dumps(user_email)

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
        console.log('[LoginBridge] doLogin called lid=' + lid + ' pwd_len=' + pwd.length);
        if (!lid || !pwd) {{ setStatus('Enter username and password.', true); return; }}
        $('btn').disabled = true;
        setStatus('Signing in...');

        var url = base().replace(/\/$/, '') + '/api/v4/users/login';
        console.log('[LoginBridge] POST ' + url);

        var xhr = new XMLHttpRequest();
        xhr.open('POST', url, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.withCredentials = true;
        xhr.onload = function () {{
            console.log('[LoginBridge] onload status=' + xhr.status);
            var token = xhr.getResponseHeader('Token');
            console.log('[LoginBridge] token=' + (token ? 'present' : 'MISSING'));
            if (xhr.status >= 200 && xhr.status < 300 && token) {{
                try {{ localStorage.setItem('MMAUTHTOKEN', token); }} catch (e) {{}}
                try {{ localStorage.setItem('storage:MMAUTHTOKEN', JSON.stringify(token)); }} catch (e) {{}}
                document.cookie = 'MMAUTHTOKEN=' + token + '; path=/; max-age=86400; SameSite=Lax';
                setStatus('Success! Loading...');
                // Let Mattermost handle team selection - don't specify team in redirect
                var redirectPath = '/channels/town-square';
                var baseUrl = base().replace(/\/$/, '');
                // Pass token via URL param to ensure server-side shim injection
                var redirectUrl = baseUrl + redirectPath + '?mm_token=' + encodeURIComponent(token);
                console.log('[LoginBridge] redirecting to', redirectUrl);
                window.location.replace(redirectUrl);
                return;
            }}
            var msg = 'Login failed (HTTP ' + xhr.status + ')';
            try {{ var b = JSON.parse(xhr.responseText || '{{}}'); if (b.message) msg = b.message; }} catch (e) {{}}
            console.log('[LoginBridge] fail msg=' + msg);
            $('btn').disabled = false;
            setStatus(msg, true);
        }};
        xhr.onerror = function () {{
            console.log('[LoginBridge] onerror — network failure');
            $('btn').disabled = false;
            setStatus('Network error — check console.', true);
        }};
        xhr.onabort = function () {{
            console.log('[LoginBridge] onabort');
            $('btn').disabled = false;
            setStatus('Request aborted.', true);
        }};
        xhr.ontimeout = function () {{
            console.log('[LoginBridge] ontimeout');
            $('btn').disabled = false;
            setStatus('Request timed out.', true);
        }};
        try {{
            xhr.send(JSON.stringify({{ login_id: lid, password: pwd }}));
            console.log('[LoginBridge] xhr.send() called');
        }} catch (e) {{
            console.log('[LoginBridge] xhr.send() threw: ' + e);
            $('btn').disabled = false;
            setStatus('Send error: ' + e.message, true);
        }}
    }}

    document.addEventListener('DOMContentLoaded', function () {{
        $('btn').addEventListener('click', doLogin);
        var hasCreds = $('lid').value && $('pwd').value;
        var existingToken = '';
        try {{ existingToken = localStorage.getItem('MMAUTHTOKEN') || ''; }} catch(e) {{}}
        if (!existingToken) {{
            var m = document.cookie.match(/MMAUTHTOKEN=([^;]+)/);
            if (m) existingToken = m[1];
        }}
        console.log('[LoginBridge] loaded. lid=' + ($('lid').value ? 'yes' : 'no') +
                    ' pwd=' + ($('pwd').value ? 'yes' : 'no') +
                    ' auto=' + hasCreds + ' hasToken=' + (existingToken ? 'yes' : 'no'));
        if (existingToken) {{
            console.log('[LoginBridge] Token already exists — redirecting to channels, skipping login');
            // Let Mattermost handle team selection - don't specify team in redirect
            window.location.replace(base().replace(/\/$/, '') + '/channels/town-square');
            return;
        }}
        if (hasCreds) {{
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

    def _credential_matches_active_user(self, request, login_id: str) -> bool:
        """Allow auto-login only when stored credentials map to the active Django user."""
        normalized = (login_id or '').strip().lower()
        if not normalized:
            return False
        user = getattr(request, 'user', None)
        candidates = {
            (getattr(user, 'username', '') or '').strip().lower(),
            (getattr(user, 'email', '') or '').strip().lower(),
        }
        candidates.discard('')
        return normalized in candidates

    def process_html_response(self, html_str, request, endpoint_url=None, *args, **kwargs):
        print(f"[MattermostPassthroughHandler] process_html_response called, path={request.path_info}, html_len={len(html_str)}")

        # Derive trigger from path for use throughout the function
        _path_parts = (getattr(request, 'path_info', '') or '').strip('/').split('/')
        _trigger = _path_parts[2] if len(_path_parts) >= 3 else "mattermost"

        # If Mattermost served its login HTML, replace entirely with our own form.
        if '/login' in (getattr(request, 'path_info', '') or ''):
            if len(_path_parts) >= 3 and _path_parts[0] == 'pt' and _path_parts[1] == 'admin':
                _proxy_prefix = f"/pt/admin/{_path_parts[2]}"
            else:
                _proxy_prefix = "/pt/admin/mattermost"
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

        # Wrap in admin template for embedded dashboard display
        from django.http import HttpResponse
        response = HttpResponse(html_str.encode('utf-8'), status=200)
        response['Content-Type'] = 'text/html; charset=utf-8'
        response['X-Frame-Options'] = 'ALLOWALL'
        from dose.passthrough.forwarding import _wrap_in_admin_template
        _endpoint_stub = type('E', (), {'endpoint_url': endpoint_url})()
        wrapped = _wrap_in_admin_template(request, response, _trigger, _endpoint_stub)
        return wrapped

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
        """Return extra_config dict for this tenant's Mattermost TenantApp.
        Uses ORM with PublicTenantAppBundleManager (search_path=public) — the records
        are global (public schema), not per-tenant-schema copies."""
        try:
            from dose.models import TenantApp
            tenant = None
            if request is not None:
                try:
                    from dose.utils import get_current_tenant
                    tenant = getattr(request, 'tenant', None) or get_current_tenant(request)
                except Exception as _te:
                    print(f"[MM LoginBridge] tenant lookup error: {_te}")
            # Tenant-specific first (public schema)
            if tenant:
                try:
                    ta = TenantApp.public_bundles.filter(
                        app_name='mattermost', tenant=tenant
                    ).exclude(extra_config={}).first()
                    if ta and ta.extra_config:
                        print(f"[MM LoginBridge] extra_config found via public tenant={tenant} keys={list(ta.extra_config.keys())}")
                        return ta.extra_config
                except Exception as _q1:
                    print(f"[MM LoginBridge] public tenant query error: {_q1}")
                # Fallback: tenant schema
                try:
                    ta = TenantApp.objects.filter(
                        app_name='mattermost', tenant=tenant
                    ).exclude(extra_config={}).first()
                    if ta and ta.extra_config:
                        print(f"[MM LoginBridge] extra_config found via tenant schema tenant={tenant} keys={list(ta.extra_config.keys())}")
                        return ta.extra_config
                except Exception as _q2:
                    print(f"[MM LoginBridge] tenant schema query error: {_q2}")
            # Fallback: any active mattermost app with credentials (public schema)
            try:
                ta = TenantApp.public_bundles.filter(
                    app_name='mattermost', status='active'
                ).exclude(extra_config={}).first()
                if ta and ta.extra_config:
                    print(f"[MM LoginBridge] extra_config found via public active fallback keys={list(ta.extra_config.keys())}")
                    return ta.extra_config
            except Exception as _q3:
                print(f"[MM LoginBridge] public active fallback error: {_q3}")
            # Fallback: any active mattermost app (tenant schema)
            try:
                ta = TenantApp.objects.filter(
                    app_name='mattermost', status='active'
                ).exclude(extra_config={}).first()
                if ta and ta.extra_config:
                    print(f"[MM LoginBridge] extra_config found via tenant active fallback keys={list(ta.extra_config.keys())}")
                    return ta.extra_config
            except Exception as _q4:
                print(f"[MM LoginBridge] tenant active fallback error: {_q4}")
            print(f"[MM LoginBridge] extra_config NOT found (tenant={tenant})")
        except Exception as exc:
            print(f"[MM LoginBridge] _get_tenantapp_extra_config outer error: {exc}")
        return {}

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
        NEVER create a server-side login session — that pushes the browser's session
        past Mattermost's per-user session limit and revokes it, causing infinite loops.
        """
        # Don't inject a session token into the login/logout request itself —
        # Mattermost rejects login attempts that carry a stale session.
        _path = (getattr(request, 'path_info', '') or '')
        if '/api/v4/users/login' in _path or '/api/v4/users/logout' in _path:
            return {}

        # BROWSER COOKIE ONLY: If the browser has MMAUTHTOKEN, return it.
        # If not, return {} — let the login bridge handle authentication.
        # Server-side logins create NEW sessions that invalidate the browser's token.
        browser_token = request.COOKIES.get('MMAUTHTOKEN') or request.COOKIES.get('mmauthtoken')
        if browser_token:
            print(f"[MM_AUTH] Browser cookie shortcut: returning MMAUTHTOKEN len={len(browser_token)}")
            return {'MMAUTHTOKEN': browser_token}

        print("[MM_AUTH] No browser MMAUTHTOKEN — returning empty cookies (login bridge will handle auth)")
        return {}

    def augment_outbound_headers(self, request, headers: dict, target_url: str) -> None:
        """Inject Authorization Bearer token for all Mattermost requests forwarded through proxy."""
        print(f'[MM_AUTH] augment_outbound_headers called for {target_url}')
        # Never inject on login/logout — Mattermost rejects requests with a stale session token.
        if '/api/v4/users/login' in (target_url or '') or '/api/v4/users/logout' in (target_url or ''):
            print('[MM_AUTH] Skipping login/logout path')
            return
        
        # PRIORITY: Browser cookie first — always fresh after successful login bridge.
        # Server cache may hold stale provisioning tokens or expired session tokens.
        all_cookies = dict(request.COOKIES)
        print(f'[MM_AUTH] Incoming cookies: {list(all_cookies.keys())}')
        print(f'[MM_AUTH] MMAUTHTOKEN cookie: {"PRESENT" if all_cookies.get("MMAUTHTOKEN") else "MISSING"}')
        print(f'[MM_AUTH] mmauthtoken cookie: {"PRESENT" if all_cookies.get("mmauthtoken") else "MISSING"}')
        print(f'[MM_AUTH] Cookie values present: {[k for k,v in all_cookies.items() if v]}')
        token = request.COOKIES.get('MMAUTHTOKEN') or request.COOKIES.get('mmauthtoken')
        _src = 'browser-cookie' if token else 'none'
        print(f'[MM_AUTH] Selected token source: {_src}')
        
        # Fallback to server cache if browser has no token (first visit)
        if not token:
            try:
                extra_config = self._get_tenantapp_extra_config(request)
                if extra_config:
                    token = (extra_config.get('mmauthtoken') or
                             extra_config.get('mm_session_token') or
                             extra_config.get('mm_token'))
                    if token:
                        _src = 'server-cache'
                        print(f'[MM_AUTH] Using server cache token')
            except Exception as exc:
                print(f'[MM_AUTH] Error getting cached token: {exc}')
        
        if token and 'Authorization' not in headers:
            headers['Authorization'] = f'Bearer {token}'
            print(f'[MM_AUTH] Injected Authorization ({_src}, token={token[:8]}...) for {target_url}')
            # Fire CORS patch once per process on first authenticated API call
            if '/api/v4/' in (target_url or '') and not MattermostPassthroughHandler._cors_patched:
                try:
                    _ep = getattr(request, '_passthrough_endpoint', None)
                    _ep_url = getattr(_ep, 'endpoint_url', None) or ''
                    self._ensure_cors_allowed(request, _ep_url.rstrip('/'), token)
                except Exception as exc:
                    print(f'[MM CORS] Fire-and-forget error: {exc}')
        elif not token:
            print(f'[MM_AUTH] NO TOKEN AVAILABLE for {target_url} — request will be unauthenticated')

    def postprocess_upstream_response(self, resp, request, **kwargs):
        """Hook to handle upstream responses - log all API calls and clear token on 401."""
        target_url = kwargs.get('endpoint_url', '')
        
        # Log ALL Mattermost API responses for debugging
        if '/api/v4/' in (target_url or ''):
            print(f'[MM_RESP] {target_url} -> HTTP {resp.status_code}')
            # Log auth-related response headers
            token_header = resp.headers.get('Token')
            if token_header:
                print(f'[MM_RESP] Token header present: {token_header[:10]}...')
        
        # If we get a 401 on ANY API call (not just /users/me), the token is invalid.
        # Clear BOTH server cache AND browser cookie to force re-auth via login bridge.
        if resp.status_code == 401 and '/api/v4/' in (target_url or ''):
            print(f'[MM_AUTH] Got 401 on {target_url} - clearing token EVERYWHERE')
            try:
                # Clear server cache
                extra_config = self._get_tenantapp_extra_config(request)
                if extra_config:
                    for key in ['mmauthtoken', 'mm_session_token', 'mm_token', 'mmauthtoken_time', 'mm_session_token_time']:
                        if key in extra_config:
                            del extra_config[key]
                    self._save_tenantapp_config(request, extra_config)
                    print(f'[MM_AUTH] Cleared invalid token from server cache')
            except Exception as exc:
                print(f'[MM_AUTH] Failed to clear server cache: {exc}')
            # We can't clear browser cookies from server-side, but the shim does this client-side.
            # Return a response that clears the cookie so the browser knows to re-auth.
            if '/users/me' in (target_url or ''):
                from django.http import HttpResponse
                clear_resp = HttpResponse(resp.content, status=resp.status_code)
                for hk, hv in resp.headers.items():
                    if hk.lower() not in ('content-length', 'transfer-encoding', 'set-cookie'):
                        clear_resp[hk] = hv
                clear_resp['Set-Cookie'] = 'MMAUTHTOKEN=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax'
                print(f'[MM_AUTH] Injected Set-Cookie to clear MMAUTHTOKEN on 401 response')
                return clear_resp
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
        # Prefer URL parameter (from login bridge redirect) first
        token = request.GET.get('mm_token') or ""
        if token:
            logger.info("[MM Shim] token from URL param, len=%d", len(token))
        else:
            # Fallback to browser cookie — it's always fresh after login bridge succeeds.
            # Server-side cache may be stale (e.g., provisioning token vs post-login session token).
            token = request.COOKIES.get('MMAUTHTOKEN') or request.COOKIES.get('mmauthtoken') or ""
            if token:
                logger.info("[MM Shim] token from browser cookie, len=%d", len(token))
            else:
                # Fallback to server-side token if browser has none
                try:
                    cookies = self.get_upstream_cookies(request) or {}
                    token = cookies.get("MMAUTHTOKEN") or ""
                    logger.info("[MM Shim] token from server, len=%d", len(token))
                except Exception as exc:
                    logger.warning("[MattermostPassthroughHandler] Token lookup failed: %s", exc)

        login_id = ""
        password = ""
        try:
            extra = self._get_tenantapp_extra_config(request) or {}
            login_id = (extra.get('mattermost_login_id') or extra.get('mm_login_id') or
                        extra.get('mattermost_username') or extra.get('login_id') or
                        getattr(getattr(request, 'user', None), 'email', '') or '')
            password = (extra.get('mattermost_password') or extra.get('mm_password') or
                        extra.get('password') or '')
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

    // Plugin diagnostic helpers (if plugin is deployed)
    function checkPluginDiagnostics() {{
        var diagUrl = PROXY + '/plugins/com.polysaas.passthrough/api/v1/diagnostics';
        console.log('[PolySaaS MM] Checking plugin diagnostics:', diagUrl);
        fetch(diagUrl, {{
            headers: {{'Authorization': 'Bearer ' + MMAUTHTOKEN}}
        }}).then(function(r) {{
            if (r.ok) {{
                return r.json();
            }}
            console.log('[PolySaaS MM] Plugin diagnostics not available (plugin may not be deployed)');
            return null;
        }}).then(function(data) {{
            if (data) {{
                console.log('[PolySaaS MM] Plugin diagnostics:', data);
            }}
        }}).catch(function(e) {{
            console.log('[PolySaaS MM] Plugin diagnostics error:', e);
        }});
    }}
    
    function checkPluginAuth() {{
        var authUrl = PROXY + '/plugins/com.polysaas.passthrough/api/v1/auth-check';
        console.log('[PolySaaS MM] Checking plugin auth:', authUrl);
        fetch(authUrl, {{
            headers: {{'Authorization': 'Bearer ' + MMAUTHTOKEN}}
        }}).then(function(r) {{
            if (r.ok) {{
                return r.json();
            }}
            console.log('[PolySaaS MM] Plugin auth check failed:', r.status);
            return null;
        }}).then(function(data) {{
            if (data) {{
                console.log('[PolySaaS MM] Plugin auth check:', data);
            }}
        }}).catch(function(e) {{
            console.log('[PolySaaS MM] Plugin auth check error:', e);
        }});
    }}
    
    // Run plugin diagnostics after a short delay
    setTimeout(function() {{
        checkPluginDiagnostics();
        checkPluginAuth();
    }}, 2000);

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

    // LOOP BREAKER: Track redirects to /login to prevent infinite loops.
    // Persisted in sessionStorage (survives page reloads), auto-resets after 2 min.
    var _mmRedirectCount = 0;
    var _mmRedirectKey = '_polysaas_mm_redirect_count';
    var _mmRedirectTimeKey = '_polysaas_mm_redirect_time';
    try {{
        var _lastTime = parseInt(sessionStorage.getItem(_mmRedirectTimeKey) || '0', 10);
        var _now = Date.now();
        if (_now - _lastTime > 120000) {{
            sessionStorage.removeItem(_mmRedirectKey);
            sessionStorage.removeItem(_mmRedirectTimeKey);
            _mmRedirectCount = 0;
        }} else {{
            _mmRedirectCount = parseInt(sessionStorage.getItem(_mmRedirectKey) || '0', 10);
        }}
    }} catch(e) {{}}
    function _mmShouldRedirect() {{
        if (_mmRedirectCount >= 3) {{
            console.error('[PolySaaS MM] LOOP BREAKER: Stopping after 3 redirects in 2 min. Manual refresh required.');
            return false;
        }}
        _mmRedirectCount++;
        try {{
            sessionStorage.setItem(_mmRedirectKey, String(_mmRedirectCount));
            sessionStorage.setItem(_mmRedirectTimeKey, String(Date.now()));
        }} catch(e) {{}}
        return true;
    }}
    function _mmClearToken() {{
        try {{ localStorage.removeItem('storage:MMAUTHTOKEN'); }} catch(_e) {{}}
        try {{ localStorage.removeItem('storage:MMAuthtokenExpiry'); }} catch(_e) {{}}
        try {{ localStorage.removeItem('MMAUTHTOKEN'); }} catch(_e) {{}}
        document.cookie = 'MMAUTHTOKEN=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax';
    }}
    function _mmRedirectToLogin() {{
        if (!_mmShouldRedirect()) return;
        console.log('[PolySaaS MM] Redirecting to login bridge');
        setTimeout(function() {{ window.location.replace(PROXY + '/login?force=1'); }}, 300);
    }}

    var _f = window.fetch;
    window.fetch = function(input, init) {{
        var original = input;
        var reqUrl = typeof input === 'string' ? input : (input && input.url ? input.url : '');
        
        // Block external analytics requests that cause CORS errors and hang the UI
        if (reqUrl.indexOf('matterlytics.com') !== -1 || 
            reqUrl.indexOf('rudderstack.com') !== -1 ||
            reqUrl.indexOf('segment.io') !== -1) {{
            console.log('[PolySaaS MM] Blocked external analytics request:', reqUrl);
            return Promise.resolve(new Response(null, {{status: 204, statusText: 'No Content'}}));
        }}
        
        if (typeof input === 'string') {{
            input = toProxy(input);
        }} else if (typeof Request !== 'undefined' && input instanceof Request) {{
            var u = toProxy(input.url);
            if (u !== input.url) input = new Request(u, input);
        }}
        
        // Block logout requests to prevent token invalidation (check both original and proxied URL)
        var proxiedUrl = typeof input === 'string' ? input : (input && input.url ? input.url : '');
        if (reqUrl.indexOf('/users/logout') !== -1 || proxiedUrl.indexOf('/users/logout') !== -1) {{
            console.log('[PolySaaS MM] Blocked logout request to preserve session:', reqUrl, '->', proxiedUrl);
            return Promise.resolve(new Response(null, {{status: 200, statusText: 'OK'}}));
        }}
        if (MMAUTHTOKEN) {{
            var reqUrl = typeof input === 'string' ? input : (input && input.url ? input.url : '');
            if (reqUrl.indexOf('/api/v4/') !== -1 || reqUrl.indexOf('/plugins/') !== -1) {{
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
        
        // Retry logic for plugin config 401 errors
        if (_reqUrlForLog.indexOf('/plugins/') !== -1) {{
            var _retryCount = 0;
            var _maxRetries = 3;
            var _retryDelay = 1000;
            
            function _retryWithBackoff(originalInput, originalInit) {{
                return new Promise(function(resolve, reject) {{
                    setTimeout(function() {{
                        console.log('[PolySaaS MM] Retrying plugin request, attempt', _retryCount + 1, ':', _reqUrlForLog.slice(0, 60));
                        _f.call(window, originalInput, originalInit).then(resolve).catch(reject);
                    }}, _retryDelay);
                }});
            }}
            
            return _prom.catch(function(err) {{
                if (_retryCount < _maxRetries && err.status === 401) {{
                    _retryCount++;
                    _retryDelay = _retryDelay * 2; // Exponential backoff
                    console.log('[PolySaaS MM] Plugin request 401, retrying with backoff:', _retryDelay, 'ms');
                    return _retryWithBackoff(input, init);
                }}
                throw err;
            }});
        }}
        
        if (_reqUrlForLog.indexOf('/users/me') !== -1) {{
            return _prom.then(function(r) {{
                console.log('[PolySaaS MM] users/me HTTP status:', r.status, r.ok ? 'OK' : 'FAIL');
                if (r.status === 401) {{
                    // Validate token one more time before declaring it invalid.
                    // The 401 might be a transient error or stale server-side cache.
                    console.log('[PolySaaS MM] Got 401 on users/me — double-checking token validity...');
                    _f.call(window, PROXY + '/api/v4/users/me', {{headers: {{'Authorization': 'Bearer ' + MMAUTHTOKEN}}}}).then(function(r2) {{
                        if (r2.status === 200) {{
                            console.log('[PolySaaS MM] Token is actually VALID — ignoring transient 401');
                        }} else {{
                            console.log('[PolySaaS MM] Token confirmed invalid — clearing and redirecting');
                            _mmClearToken();
                            _mmRedirectToLogin();
                        }}
                    }}).catch(function() {{
                        console.log('[PolySaaS MM] Token validation check failed — clearing and redirecting');
                        _mmClearToken();
                        _mmRedirectToLogin();
                    }});
                }}
                return r;
            }});
        }}
        return _prom;
    }};

    var _xo = XMLHttpRequest.prototype.open;
    var _xs = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(method, url) {{
        // Block external analytics requests that cause CORS errors and hang the UI
        if (url.indexOf('matterlytics.com') !== -1 || 
            url.indexOf('rudderstack.com') !== -1 ||
            url.indexOf('segment.io') !== -1) {{
            console.log('[PolySaaS MM] Blocked external analytics XHR:', url);
            this._blocked = true;
            return;
        }}
        // Block logout requests to prevent token invalidation
        if (url.indexOf('/users/logout') !== -1) {{
            console.log('[PolySaaS MM] Blocked logout XHR to preserve session:', url);
            this._blocked = true;
            return;
        }}
        var proxied = toProxy(url);
        if (url !== proxied) console.log('[PolySaaS MM] XHR:', method, url, '->', proxied);
        var rest = Array.prototype.slice.call(arguments, 2);
        _xo.apply(this, [method, proxied].concat(rest));
        if (proxied.indexOf('/users/me') !== -1) {{
            var _self = this;
            this.addEventListener('load', function() {{
                console.log('[PolySaaS MM] XHR users/me status:', _self.status);
                if (_self.status === 401) {{
                    console.log('[PolySaaS MM] XHR 401 on users/me — clearing and redirecting');
                    _mmClearToken();
                    _mmRedirectToLogin();
                }}
            }});
        }}
        if (MMAUTHTOKEN && (proxied.indexOf('/api/v4/') !== -1 || proxied.indexOf('/plugins/') !== -1)) {{
            try {{
                this.setRequestHeader('Authorization', 'Bearer ' + MMAUTHTOKEN);
                if (proxied.indexOf('/users/me') !== -1)
                    console.log('[PolySaaS MM] XHR Auth injected for users/me, token starts:', MMAUTHTOKEN.slice(0, 8));
                if (proxied.indexOf('/plugins/') !== -1)
                    console.log('[PolySaaS MM] XHR Auth injected for plugin endpoint:', proxied);
            }} catch(e) {{}}
        }}
    }};
    XMLHttpRequest.prototype.send = function() {{
        if (this._blocked) {{
            console.log('[PolySaaS MM] XHR send blocked (analytics)');
            return;
        }}
        _xs.apply(this, arguments);
    }};

    // WEBSOCKET HARDENING: Exponential backoff reconnection with loop breaker
    var _wsFailCount = 0;
    var _wsFailTime = 0;
    var _wsStubActive = false;
    var _wsBackoffMs = 1000; // Start with 1s backoff
    var _wsMaxBackoffMs = 30000; // Max 30s backoff
    function _wsCheckFail() {{
        var now = Date.now();
        if (now - _wsFailTime > 2000) _wsFailCount = 0;
        _wsFailCount++;
        _wsFailTime = now;
        if (_wsFailCount >= 5) {{
            console.error('[PolySaaS MM] WebSocket loop breaker: 5 rapid failures, entering silent mode for 30s');
            _wsStubActive = true;
            _wsBackoffMs = 1000; // Reset backoff
            setTimeout(function() {{ _wsStubActive = false; _wsFailCount = 0; console.log('[PolySaaS MM] WebSocket retry resumed'); }}, 30000);
        }}
    }}
    function _wsSilentStub(url) {{
        console.warn('[PolySaaS MM] WebSocket silent stub for:', url);
        var stub = {{ onopen: null, onclose: null, onmessage: null, onerror: null, readyState: 1, send: function(){{}}, close: function(){{}} }};
        setTimeout(function() {{ if (stub.onopen) stub.onopen(); }}, 0);
        return stub;
    }}
    function _wsScheduleReconnect(originalUrl, originalProtocols) {{
        if (_wsStubActive) return;
        console.log('[PolySaaS MM] Scheduling WebSocket reconnect in', _wsBackoffMs, 'ms');
        setTimeout(function() {{
            console.log('[PolySaaS MM] Attempting WebSocket reconnect...');
            var ws = (originalProtocols !== undefined) ? new _WS(originalUrl, originalProtocols) : new _WS(originalUrl);
            // Apply same error handling to reconnected socket
            var origOnError = ws.onerror;
            ws.onerror = function(ev) {{
                _wsCheckFail();
                if (origOnError) origOnError.call(ws, ev);
            }};
            // On successful connection, reset backoff
            ws.onopen = function() {{
                console.log('[PolySaaS MM] WebSocket reconnected successfully');
                _wsBackoffMs = 1000;
                _wsFailCount = 0;
            }};
            // On close, schedule another reconnect with exponential backoff
            ws.onclose = function() {{
                console.log('[PolySaaS MM] WebSocket closed, scheduling reconnect with backoff');
                _wsBackoffMs = Math.min(_wsBackoffMs * 2, _wsMaxBackoffMs);
                _wsScheduleReconnect(originalUrl, originalProtocols);
            }};
        }}, _wsBackoffMs);
    }}

    var _WS = WebSocket;
    window.WebSocket = function(url, protocols) {{
        if (_wsStubActive) return _wsSilentStub(url);
        if (typeof url === 'string') {{
            try {{
                var mmOrigin = new URL(B);
                var u = new URL(url, location.href);
                u.hostname = mmOrigin.hostname;
                u.port = mmOrigin.port || '';
                u.protocol = 'wss:';
                // Add auth token to WebSocket URL query parameters
                var token = localStorage.getItem('MMAUTHTOKEN');
                if (token && !u.searchParams.has('token')) {{
                    u.searchParams.set('token', token);
                }}
                url = u.toString();
                console.log('[PolySaaS Mattermost] WebSocket direct to MM server:', url);
            }} catch (e) {{ console.warn('[PolySaaS Mattermost] WebSocket rewrite:', e); }}
        }}
        var ws = (protocols !== undefined) ? new _WS(url, protocols) : new _WS(url);
        var origOnError = ws.onerror;
        ws.onerror = function(ev) {{
            _wsCheckFail();
            if (origOnError) origOnError.call(ws, ev);
        }};
        return ws;
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
