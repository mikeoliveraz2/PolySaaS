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
from typing import Optional

import requests
from dose.passthrough.strategies import TokenRefreshStrategyFactory

logger = logging.getLogger(__name__)

# MODULE LOAD MARKER — if this doesn't appear in terminal, old code is cached
print("[MM-HANDLER-LOAD] mattermost_handler.py loaded — v2026-05-17-phase3-strategy-factory")


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

    def _get_team_name(self, request):
        """Derive Mattermost team name for redirects."""
        team_name = ''
        try:
            extra = self._get_tenantapp_extra_config(request) or {}
            team_name = extra.get('mm_team_name', '') or extra.get('team_name', '')
        except Exception:
            pass
        if not team_name:
            try:
                t = getattr(request, 'tenant', None)
                if t:
                    schema = t.schema_name[:15].lower()
                    team_name = re.sub(r'[^a-z]', '', schema)
                    if len(team_name) < 2:
                        team_name = "team"
                    if len(team_name) > 15:
                        team_name = team_name[:15]
            except Exception:
                pass
        if not team_name:
            team_name = "polysaasdevteam"
        return team_name

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
        trigger = url_trigger_segment.strip("/")
        proxy_prefix = f"/pt/admin/{trigger}"

        # Server-side bridge login handler: JS POSTs the token here and we
        # set the cookie server-side (avoids client-side cookie being dropped).
        if request.path_info.rstrip("/") == f"{proxy_prefix}/_bridge_login" and request.method == "POST":
            return self._handle_bridge_login(request, trigger, proxy_prefix)

        if request.method != "GET":
            return None

        # Intercept both root AND /login?force=1 (login bridge redirect target)
        is_root = request.path_info.rstrip("/") == proxy_prefix
        is_login_force = (
            request.path_info.rstrip("/") == f"{proxy_prefix}/login" and 
            request.GET.get('force') == '1'
        )
        
        if not (is_root or is_login_force):
            return None

        team_name = self._get_team_name(request)
        team_redirect = f"{proxy_prefix}/{team_name}/channels/town-square"
        print(f"[MM ROOT] team_name={team_name} redirect_target={team_redirect}")

        # Check for force=1 parameter to skip token validation (used when shim detects invalid token)
        force_login = request.GET.get('force') == '1'
        
        token = request.COOKIES.get('MMAUTHTOKEN') or request.COOKIES.get('mmauthtoken')
        
        # Strip JSON quotes if present (cookie may contain "" which is JSON-encoded empty string)
        if token and token.strip() == '""':
            token = ''
        
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
            resp['X-PolySaaS-Redirect'] = 'town-square-token-present'
            return resp

        # No token OR force=1 — serve login bridge INLINE (no redirect)
        print(f"[MM ROOT] No token or force=1 — serving login bridge inline at {request.path_info}")
        return self._serve_login_bridge(request, trigger, endpoint)

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
            # First priority: encrypted credentials from session (if available)
            session_creds = PassthroughCredentialContainer.retrieve(request, app_name='mattermost')
            if session_creds:
                login_id = session_creds.get('username', '')
                password = session_creds.get('password', '')
                allow_auto_submit = bool(login_id and password)
                logger.info("[MM LoginBridge] Using credentials from encrypted session")
            
            # Fallback: credentials from database extra_config
            if not login_id or not password:
                extra = self._get_tenantapp_extra_config(request) or {}
                print(f"[MM LoginBridge] extra keys={list(extra.keys())}")
                # Mattermost-specific credentials are the only safe source for auto-submit.
                mm_login = (extra.get('mattermost_login_id') or extra.get('mm_login_id') or
                            extra.get('mattermost_username') or extra.get('mm_username') or '')
                mm_pass = (extra.get('mattermost_password') or extra.get('mm_password') or '')
                # Generic keys can still prefill for convenience, but must never auto-submit.
                fallback_login = extra.get('username') or extra.get('login_id') or ''
                fallback_pass = extra.get('password') or ''
                django_username = getattr(getattr(request, 'user', None), 'username', '') or ''
                login_id = mm_login or fallback_login or django_username or user_email
                password = mm_pass or fallback_pass
                allow_auto_submit = bool(mm_login and mm_pass)
        except Exception as exc:
            logger.warning("[MM LoginBridge] Credentials lookup failed: %s", exc)
            login_id = user_email

        print(f"[MM LoginBridge] login_id={login_id!r} password_present={bool(password)} user_email={user_email!r}")

        # Get team name for redirect after login
        team_name = ''
        if 'extra' in dir():
            team_name = extra.get('mm_team_name', '') or extra.get('team_name', '')
        if not team_name:
            try:
                extra2 = self._get_tenantapp_extra_config(request) or {}
                team_name = extra2.get('mm_team_name', '') or extra2.get('team_name', '')
            except Exception:
                pass
        # Fallback: derive from tenant schema (same logic as provisioner)
        if not team_name:
            try:
                import re
                t = getattr(request, 'tenant', None)
                if t:
                    schema = t.schema_name[:15].lower()
                    team_name = re.sub(r'[^a-z]', '', schema)
                    if len(team_name) < 2:
                        team_name = "team"
                    if len(team_name) > 15:
                        team_name = team_name[:15]
            except Exception:
                pass
        # Ultimate fallback: PolySaaS Dev Team
        if not team_name:
            team_name = "polysaasdevteam"
        team_name_js = json.dumps(team_name)
        
        # HTML-escape so a quote in the password can't break the value attribute.
        lid_attr = h(login_id, quote=True)
        pwd_attr = h(password, quote=True)
        user_email_js = json.dumps(user_email)
        allow_auto_submit_js = "true" if allow_auto_submit else "false"

        # Build URLs directly to avoid path.replace() issues with/without trailing slashes
        proxy_prefix = f"/pt/admin/{trigger}"
        login_url = f"{proxy_prefix}/api/v4/users/login"
        channels_url = f"{proxy_prefix}/channels/town-square"

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
    var teamName = {team_name_js};
    var allowAutoSubmit = {allow_auto_submit_js};
    function $(id) {{ return document.getElementById(id); }}
    function setStatus(msg, err) {{
        var s = $('status');
        s.className = err ? 'err' : '';
        s.textContent = msg;
    }}
    function base() {{
        return window.location.pathname.replace(/\\/login(\\/.*)?$/, '') || '/';
    }}
    function doLogin() {{
        var lid = $('lid').value.trim();
        var pwd = $('pwd').value;
        console.log('[LoginBridge] doLogin called lid=' + lid + ' pwd_len=' + pwd.length);
        if (!lid || !pwd) {{ setStatus('Enter username and password.', true); return; }}
        $('btn').disabled = true;
        setStatus('Signing in...');

        var url = base().replace(/\\/$/, '') + '/api/v4/users/login';
        console.log('[LoginBridge] POST ' + url);

        var xhr = new XMLHttpRequest();
        xhr.open('POST', url, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.withCredentials = true;
        xhr.onload = function () {{
            console.log('[LoginBridge] onload status=' + xhr.status);
            var token = xhr.getResponseHeader('Token');
            console.log('[LoginBridge] token from header=' + (token ? token.substring(0, 30) + '...' : 'MISSING'));
            console.log('[LoginBridge] ALL response headers: ' + xhr.getAllResponseHeaders());
            if (xhr.status >= 200 && xhr.status < 300 && token) {{
                // Keep token where Mattermost client app expects it
                try {{ localStorage.setItem('MMAUTHTOKEN', token); }} catch (e) {{}}
                try {{ localStorage.setItem('storage:MMAUTHTOKEN', JSON.stringify(token)); }} catch (e) {{}}
                // Server-side bridge: POST token to _bridge_login so cookie is set reliably
                var bridgeUrl = base().replace(/\\/$/, '') + '/_bridge_login';
                console.log('[LoginBridge] POSTing token to server bridge:', bridgeUrl);
                console.log('[LoginBridge] Token being sent: ' + (token ? token.substring(0, 30) + '...' : 'MISSING'));
                var bridgeXhr = new XMLHttpRequest();
                bridgeXhr.open('POST', bridgeUrl, true);
                bridgeXhr.setRequestHeader('Content-Type', 'application/json');
                bridgeXhr.withCredentials = true;
                bridgeXhr.onload = function() {{
                    console.log('[LoginBridge] server bridge status=' + bridgeXhr.status);
                    if (bridgeXhr.status >= 200 && bridgeXhr.status < 400) {{
                        // Server set cookie + redirect; follow its redirect
                        setStatus('Success! Loading...');
                        var redirectPath = teamName ? '/' + teamName + '/channels/town-square' : '/channels/town-square';
                        console.log('[LoginBridge] following server redirect to', redirectPath);
                        window.location.replace(base() + redirectPath);
                    }} else {{
                        setStatus('Bridge error: ' + bridgeXhr.status, true);
                    }}
                }};
                bridgeXhr.onerror = function() {{
                    console.log('[LoginBridge] server bridge onerror');
                    setStatus('Bridge network error', true);
                }};
                bridgeXhr.send(JSON.stringify({{token: token}}));
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
                    ' auto=' + hasCreds + ' allowAuto=' + (allowAutoSubmit ? 'yes' : 'no') +
                    ' hasToken=' + (existingToken ? 'yes' : 'no'));
        if (existingToken && existingToken.length > 10) {{
            console.log('[LoginBridge] Valid token already exists — server-bridging then redirecting');
            var bridgeUrl = base().replace(/\\/$/, '') + '/_bridge_login';
            var bridgeXhr2 = new XMLHttpRequest();
            bridgeXhr2.open('POST', bridgeUrl, true);
            bridgeXhr2.setRequestHeader('Content-Type', 'application/json');
            bridgeXhr2.withCredentials = true;
            bridgeXhr2.onload = function() {{
                window.location.replace(base() + '/' + teamName + '/channels/town-square');
            }};
            bridgeXhr2.onerror = function() {{
                window.location.replace(base() + '/' + teamName + '/channels/town-square');
            }};
            bridgeXhr2.send(JSON.stringify({{token: existingToken}}));
            return;
        }}
        // Auto-submit if credentials are pre-filled (from passthrough config)
        if (hasCreds) {{
            console.log('[LoginBridge] Auto-submitting with pre-filled credentials');
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

    def _handle_bridge_login(self, request, trigger, proxy_prefix):
        """
        Server-side bridge login success handler.
        The client POSTs the Mattermost token here; we set the cookie
        server-side (so it can't be dropped by browser security) and
        return a redirect to town-square.
        """
        import json
        from django.http import JsonResponse, HttpResponseRedirect

        try:
            body = json.loads(request.body.decode('utf-8', errors='ignore'))
        except Exception:
            body = {}

        token = body.get('token') or request.POST.get('token')
        if not token:
            return JsonResponse({'success': False, 'error': 'Missing token'}, status=400)

        team_name = self._get_team_name(request)
        redirect_path = f"{proxy_prefix}/{team_name}/channels/town-square"

        print(f"[MM BRIDGE] TOKEN RECEIVED: len={len(token)} preview={token[:50] if token else 'EMPTY'}")
        print(f"[MM BRIDGE] Server-side cookie set — team={team_name} redirect={redirect_path}")

        from django.http import HttpResponse
        resp = HttpResponse(f"""
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Signing in...</title></head>
<body>
<script>
(function() {{
    var token = {json.dumps(token)};
    var redirect = {json.dumps(redirect_path)};
    console.log('[Mattermost Bridge] Login successful. Setting token and redirecting to', redirect);
    try {{ localStorage.setItem('MMAUTHTOKEN', token); }} catch(e) {{}}
    try {{ localStorage.setItem('mm_auth_token', token); }} catch(e) {{}}
    try {{ localStorage.setItem('storage:MMAUTHTOKEN', JSON.stringify(token)); }} catch(e) {{}}
    try {{ localStorage.setItem('storage:MMAuthtokenExpiry', JSON.stringify(Date.now() + 108000000)); }} catch(e) {{}}
    try {{ sessionStorage.setItem('MMAUTHTOKEN', token); }} catch(e) {{}}
    document.cookie = 'MMAUTHTOKEN=' + token + '; path=/; max-age=7776000; SameSite=Lax';
    document.cookie = 'mmauthtoken=' + token + '; path=/; max-age=7776000; SameSite=Lax';
    setTimeout(function() {{
        window.location.replace(redirect);
    }}, 800);
}})();
</script>
<noscript><meta http-equiv="refresh" content="0;url={redirect_path}"></noscript>
<p style="text-align:center;margin-top:40px;font-family:sans-serif;">Signing in...</p>
</body></html>
""", content_type="text/html; charset=utf-8")
        resp.set_cookie(
            'MMAUTHTOKEN', token,
            path='/', samesite='Lax', httponly=False,
            max_age=60*60*24*90,
            secure=request.is_secure(),
        )
        # Also set lowercase variant for compatibility
        resp.set_cookie(
            'mmauthtoken', token,
            path='/', samesite='Lax', httponly=False,
            max_age=60*60*24*90,
            secure=request.is_secure(),
        )
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

        # CRITICAL FIX: Rewrite static asset URLs to point DIRECTLY to upstream origin.
        # This bypasses the Django proxy for JS/CSS bundles, eliminating 7-15s waits.
        # Only rewrite RELATIVE /static/ paths — leave absolute URLs alone.
        html_str = re.sub(
            r'(src|href)=(["\'])(/static/[^"\']*(?:\?[^"\']*)?)',
            lambda m: f'{m.group(1)}={m.group(2)}{base_origin}{m.group(3)}{m.group(2)}',
            html_str,
            flags=re.IGNORECASE,
        )

        # Inject the full client shim into every proxied HTML page so the
        # auto-login watcher runs on /login regardless of navigation path.
        if '<head' in html_str.lower():
            print(f"[MM HANDLER] Injecting shim into HTML, proxy_prefix={proxy_prefix}")
            html_str = self._inject_client_shim(html_str, base_origin, request, proxy_prefix, endpoint_url=endpoint_url)
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
                except Exception:
                    pass
            # Tenant-specific first
            if tenant:
                ta = TenantApp.public_bundles.filter(
                    app_name='mattermost', tenant=tenant
                ).exclude(extra_config={}).first()
                if ta and ta.extra_config:
                    print(f"[MM LoginBridge] extra_config found via tenant={tenant} keys={list(ta.extra_config.keys())}")
                    return ta.extra_config
            # Fallback: any active mattermost app with credentials
            ta = TenantApp.public_bundles.filter(
                app_name='mattermost', status='active'
            ).exclude(extra_config={}).first()
            if ta and ta.extra_config:
                print(f"[MM LoginBridge] extra_config found via active fallback keys={list(ta.extra_config.keys())}")
                return ta.extra_config
            print(f"[MM LoginBridge] extra_config NOT found (tenant={tenant})")
        except Exception as exc:
            print(f"[MM LoginBridge] _get_tenantapp_extra_config error: {exc}")
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
        
        # BROWSER COOKIE ONLY — server-cached provisioning tokens (PATs) can be revoked
        # when Mattermost's DB resets, causing 401 loops. Only a live browser session token
        # is guaranteed fresh. If no cookie exists, send unauthenticated → login bridge handles.
        all_cookies = dict(request.COOKIES)
        print(f'[MM_AUTH] Incoming cookies: {list(all_cookies.keys())}')
        print(f'[MM_AUTH] MMAUTHTOKEN cookie: {"PRESENT" if all_cookies.get("MMAUTHTOKEN") else "MISSING"}')
        print(f'[MM_AUTH] mmauthtoken cookie: {"PRESENT" if all_cookies.get("mmauthtoken") else "MISSING"}')
        token = request.COOKIES.get('MMAUTHTOKEN') or request.COOKIES.get('mmauthtoken')
        _src = 'browser-cookie' if token else 'none'
        print(f'[MM_AUTH] Selected token source: {_src}')
        
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

    def _regenerate_mattermost_token(self, request, username: str, password: str, mm_url: str = None) -> Optional[str]:
        """
        Regenerate a Mattermost session token using username and password.
        
        Delegates to TokenRefreshStrategyFactory for the actual token refresh logic.
        This method maintains backward compatibility while using the new strategy pattern.
        
        Called when current token is invalid (401) to attempt automatic re-authentication
        without forcing the user back to the login bridge.
        
        Args:
            request: Django request object
            username: Mattermost login ID or username
            password: User's Mattermost password
            mm_url: Mattermost base URL (e.g., https://mm.example.com). If not provided, tries to infer from request.
            
        Returns:
            str: New session token if successful, None otherwise
        """
        print(f"[MM_REGEN] CALLED: username={username!r} password_len={len(password) if password else 0} mm_url={mm_url}")
        try:
            # Get Mattermost URL from parameter or infer from request context
            if not mm_url:
                try:
                    _ep = getattr(request, '_passthrough_endpoint', None)
                    mm_url = getattr(_ep, 'endpoint_url', None) if _ep else None
                except:
                    pass
            
            if not mm_url:
                logger.warning("[MM_REGEN] No Mattermost URL provided or available in request")
                print("[MM_REGEN] No Mattermost URL provided or available in request")
                return None
            
            print(f"[MM_REGEN] Attempting token refresh: mm_url={mm_url} username={username}")
            
            # Use TokenRefreshStrategyFactory to get the Mattermost strategy
            # and delegate the token refresh to it
            strategy = TokenRefreshStrategyFactory.get_strategy('mattermost')
            print(f"[MM_REGEN] Got strategy: {type(strategy).__name__}")
            token = strategy.refresh(request, mm_url, username, password)
            
            print(f"[MM_REGEN] Strategy returned token: len={len(token) if token else 0} preview={token[:30] if token else 'NONE'}")
            if token:
                logger.info("[MM_REGEN] Token regenerated for user %s via strategy", username)
                print(f"[MM_REGEN] Token regenerated successfully for {username}")
                return token
            else:
                logger.warning("[MM_REGEN] Token refresh failed via strategy for user %s", username)
                print(f"[MM_REGEN] Token refresh failed for {username}")
                return None
                
        except Exception as exc:
            logger.warning("[MM_REGEN] Token regeneration failed: %s", exc)
            return None

    def postprocess_upstream_response(self, resp, request, **kwargs):
        """Hook to handle upstream responses - attempt token refresh on 401 using encrypted session."""
        target_url = kwargs.get('target_url', '')
        endpoint_url = kwargs.get('endpoint_url', '')  # Base Mattermost URL
        
        # Log ALL Mattermost API responses for debugging
        if '/api/v4/' in (target_url or ''):
            print(f'[MM_RESP] {target_url} -> HTTP {resp.status_code}')
            # Log auth-related response headers
            token_header = resp.headers.get('Token')
            if token_header:
                print(f'[MM_RESP] Token header present: {token_header[:10]}...')
        
        # If we get a 401 on ANY API call (not just /users/me), the token might be invalid.
        # Try to regenerate it using encrypted session credentials before clearing.
        if resp.status_code == 401 and '/api/v4/' in (target_url or ''):
            print(f'[MM_AUTH] Got 401 on {target_url} - attempting token refresh from session')
            
            # Try to regenerate token using password from encrypted session
            try:
                from dose.passthrough.credential_container import PassthroughCredentialContainer
                session_creds = PassthroughCredentialContainer.retrieve(request, 'mattermost')
                
                if session_creds and session_creds.get('password'):
                    username = session_creds.get('username', '')
                    password = session_creds.get('password', '')
                    
                    print(f'[MM_AUTH] Attempting to regenerate token for {username}')
                    new_token = self._regenerate_mattermost_token(request, username, password, mm_url=endpoint_url)
                    
                    if new_token:
                        print(f'[MM_AUTH] Token regenerated successfully - setting cookie')
                        # Create response with new token in cookie
                        from django.http import HttpResponse
                        # Return empty 200 OK response - client will retry with new cookie
                        regen_resp = HttpResponse('', status=200)
                        regen_resp['X-PolySaaS-Token-Refreshed'] = 'true'
                        regen_resp['Set-Cookie'] = f'MMAUTHTOKEN={new_token}; path=/; SameSite=Lax'
                        return regen_resp
                    else:
                        print(f'[MM_AUTH] Token regeneration failed - falling back to clear+reauth')
                else:
                    print(f'[MM_AUTH] No password in session - cannot regenerate token')
                    
            except Exception as exc:
                print(f'[MM_AUTH] Token regeneration attempt failed: {exc}')
                logger.warning("[MM_AUTH] Regeneration exception: %s", exc)
            
            # Fallback: If regeneration not available or failed, clear token and force re-auth
            print(f'[MM_AUTH] Clearing token EVERYWHERE (regeneration failed)')
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
        self, request, proxy_prefix: str, base_origin: str, endpoint_url=None
    ) -> str:
        """
        Full client shim for Mattermost in PolySaaS: MMAUTHTOKEN, webpack public path,
        fetch/XHR/WebSocket → proxy, attribute/prototype patching (matches generated handler).
        Display shell must include network patches or API/WS stay on the admin origin → spinner.
        """
        # Prefer browser cookie first — it's always fresh after login bridge succeeds.
        # Server-side cache may be stale (e.g., provisioning token vs post-login session token).
        token = request.COOKIES.get('MMAUTHTOKEN') or request.COOKIES.get('mmauthtoken') or ""
        print(f"[MM SHIM] Reading token from request.COOKIES: MMAUTHTOKEN={request.COOKIES.get('MMAUTHTOKEN')!r} mmauthtoken={request.COOKIES.get('mmauthtoken')!r}")
        if token:
            logger.info("[MM Shim] token from browser cookie, len=%d", len(token))
            print(f"[MM SHIM] Token from browser cookie: len={len(token)} preview={token[:30] if token else 'EMPTY'}")
        else:
            # Fallback to server-side token if browser has none
            try:
                cookies = self.get_upstream_cookies(request) or {}
                token = cookies.get("MMAUTHTOKEN") or ""
                logger.info("[MM Shim] token from server, len=%d", len(token))
                print(f"[MM SHIM] Token from server cache: len={len(token)} preview={token[:30] if token else 'EMPTY'}")
            except Exception as exc:
                logger.warning("[MattermostPassthroughHandler] Token lookup failed: %s", exc)
                print(f"[MM SHIM] Token lookup exception: {exc}")

        login_id = ""
        password = ""
        try:
            # First priority: encrypted credentials from session
            from dose.passthrough.credential_container import PassthroughCredentialContainer
            session_creds = PassthroughCredentialContainer.retrieve(request, app_name='mattermost')
            print(f"[MM SHIM] PassthroughCredentialContainer.retrieve returned: {session_creds}")
            if session_creds:
                login_id = session_creds.get('username', '')
                password = session_creds.get('password', '')
                logger.info("[MM Shim] Using credentials from encrypted session")
                print(f"[MM SHIM] Got credentials from session: login_id={login_id!r} password_len={len(password) if password else 0}")
                
                # NEW: If no token in cookie but we have credentials, try to regenerate token immediately
                # This eliminates the spinner/manual-login on first page load after provisioning
                if not token and login_id and password:
                    try:
                        mm_url = endpoint_url or self._get_tenantapp_extra_config(request).get('app_url') or \
                                 self._get_tenantapp_extra_config(request).get('url')
                        if not mm_url:
                            # Fallback: derive from proxy_prefix
                            mm_url = f"https://{proxy_prefix.split('/')[-1]}"
                        print(f"[MM SHIM] Conditions met: token_empty={not token} login_id={login_id!r} password_len={len(password)}")
                        print(f"[MM SHIM] No browser token, attempting regeneration from session credentials (url={mm_url}) (endpoint_url={endpoint_url})")
                        regen_token = self._regenerate_mattermost_token(request, login_id, password, mm_url=mm_url)
                        if regen_token:
                            token = regen_token
                            print(f"[MM SHIM] Token regenerated successfully, len={len(token)}")
                        else:
                            print(f"[MM SHIM] Token regeneration failed, will require manual login")
                    except Exception as exc:
                        print(f"[MM SHIM] Token regeneration exception: {exc}")
                else:
                    print(f"[MM SHIM] Regen conditions NOT met: token={bool(token)} login_id={bool(login_id)} password={bool(password)}")
            else:
                print(f"[MM SHIM] NO SESSION CREDS found from PassthroughCredentialContainer")
            
            # Fallback: database extra_config
            if not login_id or not password:
                extra = self._get_tenantapp_extra_config(request) or {}
                login_id = (extra.get('mattermost_login_id') or extra.get('mm_login_id') or
                            extra.get('mattermost_username') or extra.get('mm_username') or '')
                password = (extra.get('mattermost_password') or extra.get('mm_password') or
                            '')
                print(f"[MM SHIM] Fallback to database extra_config: login_id={login_id!r} password_len={len(password) if password else 0}")
        except Exception as exc:
            logger.warning("[MattermostPassthroughHandler] Credentials lookup failed: %s", exc)

        token_js = json.dumps(token)
        login_id_js = json.dumps(login_id)
        password_js = json.dumps(password)
        proxy_js = json.dumps(proxy_prefix)
        base_js = json.dumps(base_origin.rstrip("/"))
        print(f"[MM SHIM INJECT] token_len={len(token)} token_preview={token[:20] if token else 'NONE'} endpoint_url={endpoint_url}")
        
        # PAUSE FOR DEBUG CAPTURE
        import time
        print("\n" * 3)
        print("╔" + "="*78 + "╗")
        print("║" + " "*78 + "║")
        print("║" + "[MM SHIM TOKEN DEBUG] --- CRITICAL INFO BELOW ---".center(78) + "║")
        print("║" + f"Token length: {len(token)} chars".center(78) + "║")
        print("║" + f"Token preview: {token[:30] if token else 'NONE'}".center(78) + "║")
        print("║" + f"Endpoint: {endpoint_url}".center(78) + "║")
        print("║" + " "*78 + "║")
        print("╚" + "="*78 + "╝")
        print("\n" * 3)

        return f"""
<script data-polysaas-mattermost-shim="1">
(function() {{
    // PolySaaS Mattermost v6 - Force Token + Early Run
    console.log('[PolySaaS MM v6] Aggressive token restore');
    var _mmCookieMatch = document.cookie.match(/MMAUTHTOKEN=([^;]+)/);
    if (_mmCookieMatch) {{
        try {{ localStorage.setItem('MMAUTHTOKEN', _mmCookieMatch[1]); }} catch(e) {{}}
        try {{ localStorage.setItem('mm_auth_token', _mmCookieMatch[1]); }} catch(e) {{}}
        console.log('[PolySaaS MM] Token forced into localStorage');
    }}
    var B = {base_js};
    var PROXY = {proxy_js};
    var O = window.location.origin;
    var _serverToken = {token_js};
    var _lsToken = '';
    try {{ _lsToken = localStorage.getItem('MMAUTHTOKEN') || ''; }} catch(e) {{}}
    var MMAUTHTOKEN = _serverToken || _lsToken || '';
    var MM_LOGIN_ID = {login_id_js};
    var MM_PASSWORD = {password_js};

    // Spy on localStorage reads to diagnose what key Mattermost uses for the auth token
    // Intercept localStorage reads so Mattermost always sees the token even if
    // it was cleared or never stored.  Also read dynamically from cookie at request time.
    function _getTokenFromCookie() {{
        var m = document.cookie.match(/MMAUTHTOKEN=([^;]+)/);
        return m ? m[1] : '';
    }}
    function _getToken() {{
        if (MMAUTHTOKEN) return MMAUTHTOKEN;
        var t = _getTokenFromCookie();
        if (t) return t;
        try {{ t = localStorage.getItem('MMAUTHTOKEN') || ''; }} catch(e) {{}}
        return t;
    }}
    var _lsGet = Storage.prototype.getItem;
    var _lsSet = Storage.prototype.setItem;
    Storage.prototype.getItem = function(key) {{
        var val = _lsGet.call(this, key);
        // Inject token when Mattermost reads auth keys and value is missing
        if ((key === 'MMAUTHTOKEN' || key === 'mm_auth_token' || key === 'storage:MMAUTHTOKEN') && !val) {{
            var t = _getTokenFromCookie();
            if (t) {{
                val = t;
                try {{ _lsSet.call(this, key, val); }} catch(e) {{}}
                console.log('[PolySaaS MM] Injected token into localStorage.getItem("' + key + '")');
            }}
        }}
        if (key && (key.indexOf('MMAUTHTOKEN') !== -1 || key.indexOf('MMAuth') !== -1 ||
                    key.indexOf('persist:') !== -1 || key.indexOf('credentials') !== -1)) {{
            console.log('[PolySaaS MM] localStorage.getItem("' + key + '") =>', val ? val.slice(0, 60) : 'null');
        }}
        return val;
    }};
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
        console.log('[PolySaaS MM] Token set in localStorage, reloading page for app to initialize with token');
        window.location.reload();
        return;
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
                return /\\/login(\\/.*)?$/.test(p);
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

    // Also intercept direct window.location assignments — Mattermost sometimes
    // uses location.href = '/login' which bypasses pushState hooks.
    (function(){{
        var _locReplace = window.location.replace;
        window.location.replace = function(url) {{
            if (typeof url === 'string') {{
                // Catch login redirects
                if (/\\/login(\\/|$|\\?)/.test(url)) {{
                    console.log('[PolySaaS MM] Intercept location.replace(/login)');
                    _locReplace.call(window.location, PROXY + '/login?force=1');
                    return;
                }}
                // Catch expired session redirects
                if (/extra=expired/.test(url)) {{
                    console.log('[PolySaaS MM] Intercept location.replace with extra=expired -> redirect to login bridge');
                    _locReplace.call(window.location, PROXY + '/login?force=1');
                    return;
                }}
            }}
            return _locReplace.call(window.location, url);
        }};
        var _locAssign = window.location.assign;
        window.location.assign = function(url) {{
            if (typeof url === 'string') {{
                // Catch login redirects
                if (/\\/login(\\/|$|\\?)/.test(url)) {{
                    console.log('[PolySaaS MM] Intercept location.assign(/login)');
                    _locAssign.call(window.location, PROXY + '/login?force=1');
                    return;
                }}
                // Catch expired session redirects
                if (/extra=expired/.test(url)) {{
                    console.log('[PolySaaS MM] Intercept location.assign with extra=expired -> redirect to login bridge');
                    _locAssign.call(window.location, PROXY + '/login?force=1');
                    return;
                }}
            }}
            return _locAssign.call(window.location, url);
        }};
        // Polling fallback DISABLED — interferes with normal Mattermost auth redirects
        // The pushState/location.assign/replace interceptors are sufficient
    }})();

    window.__webpack_public_path__ = B + '/static/';
    window.basename = PROXY;

    // Periodic token reinjection — keeps localStorage in sync with cookie
    setInterval(function() {{
        var t = _getTokenFromCookie();
        if (t) {{
            try {{ localStorage.setItem('MMAUTHTOKEN', t); }} catch(e) {{}}
            try {{ localStorage.setItem('mm_auth_token', t); }} catch(e) {{}}
            try {{ localStorage.setItem('storage:MMAUTHTOKEN', JSON.stringify(t)); }} catch(e) {{}}
        }}
    }}, 3000);

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
        if (typeof input === 'string') {{
            input = toProxy(input);
        }} else if (typeof Request !== 'undefined' && input instanceof Request) {{
            var u = toProxy(input.url);
            if (u !== input.url) input = new Request(u, input);
        }}
        var _token = _getToken();
        if (_token) {{
            var reqUrl = typeof input === 'string' ? input : (input && input.url ? input.url : '');
            if (reqUrl.indexOf('/api/v4/') !== -1) {{
                init = Object.assign({{}}, init || {{}});
                if (!init.headers) {{
                    init.headers = {{'Authorization': 'Bearer ' + _token}};
                }} else if (typeof init.headers.has === 'function') {{
                    init.headers.set('Authorization', 'Bearer ' + _token);
                }} else {{
                    init.headers = Object.assign({{}}, init.headers, {{'Authorization': 'Bearer ' + _token}});
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
                if (r.status === 401) {{
                    console.log('[PolySaaS MM] Got 401 on users/me — clearing token and redirecting to login');
                    _mmClearToken();
                    _mmRedirectToLogin();
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
                if (_self.status === 401) {{
                    console.log('[PolySaaS MM] XHR Got 401 on users/me — clearing token and redirecting to login');
                    _mmClearToken();
                    _mmRedirectToLogin();
                }}
            }});
        }}
        var _xhrToken = _getToken();
        if (_xhrToken && proxied.indexOf('/api/v4/') !== -1) {{
            try {{
                this.setRequestHeader('Authorization', 'Bearer ' + _xhrToken);
                if (proxied.indexOf('/users/me') !== -1)
                    console.log('[PolySaaS MM] XHR Auth injected for users/me, token starts:', _xhrToken.slice(0, 8));
            }} catch(e) {{}}
        }}
    }};

    // WEBSOCKET HARDENING: After 5 rapid failures (< 2s each), return a silent stub
    // to stop reconnect spam. Retries after 30s.
    var _wsFailCount = 0;
    var _wsFailTime = 0;
    var _wsStubActive = false;
    function _wsCheckFail() {{
        var now = Date.now();
        if (now - _wsFailTime > 2000) _wsFailCount = 0;
        _wsFailCount++;
        _wsFailTime = now;
        if (_wsFailCount >= 5) {{
            console.error('[PolySaaS MM] WebSocket loop breaker: 5 rapid failures, entering silent mode for 30s');
            _wsStubActive = true;
            setTimeout(function() {{ _wsStubActive = false; _wsFailCount = 0; console.log('[PolySaaS MM] WebSocket retry resumed'); }}, 30000);
        }}
    }}
    function _wsSilentStub(url) {{
        console.warn('[PolySaaS MM] WebSocket silent stub for:', url);
        var stub = {{ onopen: null, onclose: null, onmessage: null, onerror: null, readyState: 1, send: function(){{}}, close: function(){{}} }};
        setTimeout(function() {{ if (stub.onopen) stub.onopen(); }}, 0);
        return stub;
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

    // Fallback: if still on /login or spinner visible after 1.2s, force redirect to Town Square
    setTimeout(function() {{
        var onLogin = location.pathname.indexOf('/login') !== -1;
        var hasSpinner = !!document.querySelector('.spinner, .loading-spinner, .initial-loading-screen, .app__body .loading');
        if (onLogin || hasSpinner) {{
            console.log('[PolySaaS MM] Spinner/login still present after 1.2s — forcing Town Square redirect');
            window.location.replace(PROXY);
        }}
    }}, 1200);
}})();
</script>
"""

    def _inject_client_shim(self, html, base_origin, request, proxy_prefix, endpoint_url=None):
        """Inject full Mattermost shim first in <head>."""
        shim = self._mattermost_display_shim_html(
            request, proxy_prefix, base_origin, endpoint_url=endpoint_url
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
