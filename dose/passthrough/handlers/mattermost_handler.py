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
from urllib.parse import parse_qsl, urlencode, urlparse

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

    def should_follow_upstream_redirects(self, request, target_url: str, upstream_path: str) -> bool:
        """Follow document GET redirects inside the handler so Mattermost auth hops do not escape the passthrough path."""
        if request.method != 'GET':
            return False

        path = (upstream_path or '').lower()
        if any(path.startswith(prefix) for prefix in ('/api/', '/plugins/', '/boards/', '/calls/', '/websocket')):
            return False

        last_segment = path.rsplit('/', 1)[-1]
        if '.' in last_segment:
            return False

        accept = (request.headers.get('Accept', '') or '').lower()
        return 'text/html' in accept or not accept

    def _get_team_name(self, request, endpoint=None):
        """Resolve the Mattermost team slug used for post-login redirects."""
        try:
            extra = self._get_tenantapp_extra_config(request) or {}
            team_name = self._resolve_team_name(request, extra, endpoint=endpoint)
            if team_name:
                return team_name
        except Exception:
            pass
        return 'polysaas-dev-team'

    def _normalize_team_candidate(self, value: str) -> str:
        value = (value or '').strip().lower()
        if not value:
            return ''
        value = re.sub(r'[^a-z0-9-]+', '-', value)
        value = re.sub(r'-+', '-', value).strip('-')
        return value

    def _resolve_team_name(self, request, extra: dict, endpoint=None) -> str:
        stored_team = (extra.get('mm_team_name') or extra.get('team_name') or '').strip()
        stored_team_id = (extra.get('mm_team_id') or extra.get('team_id') or '').strip()
        candidates = {
            stored_team.lower(),
            self._normalize_team_candidate(stored_team),
        }
        candidates.discard('')

        token = (
            request.COOKIES.get('MMAUTHTOKEN')
            or request.COOKIES.get('mmauthtoken')
            or extra.get('mmauthtoken')
            or extra.get('mm_session_token')
            or extra.get('mm_token')
            or ''
        )
        mm_origin = (
            extra.get('mm_url')
            or extra.get('mattermost_url')
            or extra.get('mm_origin')
            or getattr(endpoint, 'endpoint_url', '')
            or getattr(getattr(request, '_passthrough_endpoint', None), 'endpoint_url', '')
            or ''
        ).rstrip('/')

        if token and mm_origin:
            try:
                import requests as _req

                teams_resp = _req.get(
                    f'{mm_origin}/api/v4/users/me/teams',
                    headers={'Authorization': f'Bearer {token}'},
                    timeout=10,
                )
                if teams_resp.status_code == 200:
                    teams = teams_resp.json() or []
                    if stored_team_id:
                        for team in teams:
                            if str(team.get('id') or '') == stored_team_id and team.get('name'):
                                return team['name']
                    for team in teams:
                        team_name = (team.get('name') or '').strip()
                        display_name = (team.get('display_name') or '').strip()
                        team_candidates = {
                            team_name.lower(),
                            display_name.lower(),
                            self._normalize_team_candidate(display_name),
                        }
                        if candidates & team_candidates and team_name:
                            return team_name
                    if teams:
                        first_name = (teams[0].get('name') or '').strip()
                        if first_name:
                            return first_name
                else:
                    print(f'[MM TEAM] users/me/teams failed: {teams_resp.status_code}')
            except Exception as exc:
                print(f'[MM TEAM] team lookup failed: {exc}')

        if stored_team:
            return self._normalize_team_candidate(stored_team) or stored_team
        return ''

    _cors_patched = False  # class-level flag: only patch once per process

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

    def _get_runtime_mattermost_admin_token(self) -> str:
        """Prefer the deployment PAT for config operations like AllowCorsFrom patching."""
        try:
            from django.conf import settings

            token = (getattr(settings, 'MATTERMOST_ADMIN_TOKEN', '') or '').strip()
            if token:
                return token
        except Exception:
            pass

        try:
            from django.db import connection
            from parameters.crypto import decrypt_json_dict

            with connection.cursor() as cur:
                cur.execute("SET search_path TO public,pg_catalog")
                cur.execute(
                    """SELECT encrypted_payload, param2
                       FROM parameters_parameter
                       WHERE matchingKey = %s
                       ORDER BY sequence ASC
                       LIMIT 1""",
                    ['MattermostProvisioningService'],
                )
                row = cur.fetchone()
            if not row:
                return ''

            encrypted_payload, param2 = row
            if encrypted_payload:
                secrets = decrypt_json_dict(encrypted_payload) or {}
                token = (
                    secrets.get('admin_token')
                    or secrets.get('MATTERMOST_ADMIN_TOKEN')
                    or ''
                ).strip()
                if token:
                    return token

            token = (param2 or '').strip()
            if token and token != 'N/A':
                return token
        except Exception as exc:
            print(f'[MM CORS] Admin token lookup failed: {exc}')

        return ''

    def _prefix_proxy_path(self, value: str, proxy_prefix: str) -> str:
        if not value or not value.startswith('/'):
            return value
        if value == proxy_prefix or value.startswith(proxy_prefix + '/'):
            return value
        if value.startswith('/pt/admin/'):
            return value
        return f'{proxy_prefix}{value}'

    def _rewrite_asset_url(self, value: str, base_origin: str, proxy_prefix: str) -> str:
        if not value:
            return value
        if value.startswith(base_origin):
            return value
        if value.startswith(proxy_prefix + '/static/'):
            return f'{base_origin}{value[len(proxy_prefix):]}'
        if value.startswith('http://') or value.startswith('https://') or value.startswith('//'):
            return value
        if value.startswith('/static/'):
            return f'{base_origin}{value}'
        if value.startswith('static/'):
            return f"{base_origin}/{value}"
        if value.startswith('/pt/admin/'):
            return value
        if value.startswith('/'):
            return f'{base_origin}{value}'
        return value

    def _proxy_prefix_from_request(self, request) -> str:
        path = getattr(request, 'path_info', '') or ''
        parts = path.strip('/').split('/')
        if len(parts) >= 3 and parts[0] == 'pt' and parts[1] == 'admin':
            return f'/{parts[0]}/{parts[1]}/{parts[2]}'
        return ''

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
        if resp.status_code not in (301, 302, 303, 307, 308):
            return resp

        location = (resp.headers.get('Location') or '').strip()
        if not location:
            return resp

        proxy_prefix = self._proxy_prefix_from_request(request)
        if not proxy_prefix:
            return resp

        request_origin = request.build_absolute_uri('/').rstrip('/')
        upstream_origin = endpoint_url.rstrip('/')
        request_host = (urlparse(request_origin).netloc or '').lower()

        absolute_location = location
        if location.startswith('/'):
            absolute_location = request_origin + location
        elif not re.match(r'^https?://', location, re.IGNORECASE):
            absolute_location = request_origin + '/' + location.lstrip('/')

        parsed = urlparse(absolute_location)
        query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
        query = dict(query_pairs)
        redirect_to = (query.get('redirect_to') or '').strip()

        if redirect_to.startswith(upstream_origin):
            redirect_to = redirect_to[len(upstream_origin):] or '/'
        elif redirect_to.startswith(request_origin):
            redirect_to = redirect_to[len(request_origin):] or '/'

        if redirect_to.startswith('/') and not redirect_to.startswith('/pt/admin/'):
            query['redirect_to'] = f'{proxy_prefix}{redirect_to}'

        same_host_redirect = (parsed.netloc or '').lower() == request_host
        root_escape = parsed.path in ('', '/') and same_host_redirect
        expired_redirect = query.get('extra') == 'expired'

        if root_escape and expired_redirect:
            login_query = [('force', '1')]
            if query.get('redirect_to'):
                login_query.append(('redirect_to', query['redirect_to']))
            normalized = f"{upstream_origin}/login?{urlencode(login_query)}"
            resp.headers['Location'] = normalized
            print(f"[MM REDIRECT] expired root redirect normalized: {location} -> {normalized}")
            return resp

        if same_host_redirect:
            normalized = f"{upstream_origin}{parsed.path or '/'}"
            if query:
                normalized += '?' + urlencode(list(query.items()))
            resp.headers['Location'] = normalized
            print(f"[MM REDIRECT] same-host redirect normalized: {location} -> {normalized}")

        return resp

    def _ensure_cors_allowed(self, request, mm_origin, token):
        """Patch Mattermost's AllowCorsFrom once per process so WebSocket connections succeed."""
        if MattermostPassthroughHandler._cors_patched:
            return
        try:
            import requests as _req
            polysaas_origin = request.build_absolute_uri('/').rstrip('/')
            auth_token = self._get_runtime_mattermost_admin_token() or token
            if not auth_token:
                print('[MM CORS] No token available for config check')
                return
            cfg_resp = _req.get(
                f'{mm_origin}/api/v4/config',
                headers={'Authorization': f'Bearer {auth_token}'},
                timeout=10,
            )
            if cfg_resp.status_code != 200:
                print(f"[MM CORS] Cannot fetch config: {cfg_resp.status_code}")
                return
            cfg = cfg_resp.json()
            current = cfg.get('ServiceSettings', {}).get('AllowCorsFrom', '') or ''
            if current.strip() == '*':
                print('[MM CORS] AllowCorsFrom already set to *')
                MattermostPassthroughHandler._cors_patched = True
                return
            if polysaas_origin in current:
                print(f"[MM CORS] Already allowed: {current}")
                MattermostPassthroughHandler._cors_patched = True
                return
            new_val = f"{current},{polysaas_origin}" if current else polysaas_origin
            patch = {'ServiceSettings': {'AllowCorsFrom': new_val}}
            patch_resp = _req.put(
                f'{mm_origin}/api/v4/config/patch',
                json=patch,
                headers={'Authorization': f'Bearer {auth_token}'},
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
                   to /channels/town-square; otherwise serve login bridge
                   INLINE (no redirect to /login — that caused the loop).
        All non-root paths return None immediately so the forwarder handles them.
        """
        if request.method != "GET":
            return None
        print('[MM ROOT] Preserving native upstream root/login document')
        return None

    def _serve_login_bridge(self, request, trigger, endpoint):
        """Plain HTML login bridge. No React, no frameworks. Just a form + XHR."""
        from django.http import HttpResponse
        from django.conf import settings
        from html import escape as h
        from dose.passthrough.credential_container import PassthroughCredentialContainer

        user_email = getattr(getattr(request, 'user', None), 'email', '') or ''
        login_id = ""
        password = ""
        allow_auto_submit = False
        try:
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

            if not login_id or not password:
                extra = self._get_tenantapp_extra_config(request) or {}
                mm_login = (extra.get('mattermost_login_id') or extra.get('mm_login_id') or
                            extra.get('mattermost_username') or extra.get('mm_username') or '')
                mm_pass = (extra.get('mattermost_password') or extra.get('mm_password') or '')
                fallback_login = extra.get('username') or extra.get('login_id') or ''
                fallback_pass = extra.get('password') or ''
                default_pass = getattr(settings, 'POLYSAAS_APP_ADMIN_PASSWORD', 'PolySaaS2026!') or ''
                django_username = getattr(getattr(request, 'user', None), 'username', '') or ''
                candidate_login = mm_login or fallback_login or django_username or user_email
                if self._credential_matches_active_user(request, candidate_login):
                    login_id = candidate_login
                    password = mm_pass or fallback_pass or default_pass
                else:
                    login_id = django_username or user_email
                    password = ''
                    logger.info("[MM LoginBridge] Refusing auto-submit for stored credentials that do not match the active user")
                allow_auto_submit = bool(login_id and password)
        except Exception as exc:
            logger.warning("[MM LoginBridge] Credentials lookup failed: %s", exc)
            login_id = user_email

        logger.info("[MM LoginBridge] login_id=%r len=%d password_present=%s",
                    login_id, len(login_id or ''), bool(password))

        # HTML-escape so a quote in the password can't break the value attribute.
        lid_attr = h(login_id, quote=True)
        pwd_attr = h(password, quote=True)
        allow_auto_submit_js = "true" if allow_auto_submit else "false"
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
    function successTarget() {{
        try {{
            var current = new URL(window.location.href);
            var redirectTo = current.searchParams.get('redirect_to') || '';
            if (redirectTo) return redirectTo;
        }} catch (e) {{}}
        return base();
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
                try {{ localStorage.setItem('storage:MMAuthtokenExpiry', JSON.stringify(Date.now() + 108000000)); }} catch (e) {{}}
                document.cookie = 'MMAUTHTOKEN=' + token + '; path=/; max-age=86400; SameSite=Lax';
                try {{ window.MMAUTHTOKEN = token; }} catch (e) {{}}
                setStatus('Success! Loading...');
                var target = successTarget();
                console.log('[LoginBridge] success target:', target);
                window.location.replace(target);
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
        if ({allow_auto_submit_js} && $('lid').value && $('pwd').value) {{
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
    def process_html_response(self, response_content, request, endpoint=None, endpoint_url=None):
        """Full rewrite + remove restrictive CSP header"""
        if isinstance(response_content, bytes):
            try:
                html = response_content.decode('utf-8')
            except Exception as e:
                print(f"[MM REWRITE] Decode failed: {e}")
                return str(response_content)
        else:
            html = str(response_content)

        upstream = "https://polysaas-mattermost.onrender.com"
        print(f"[MM REWRITE] === START REWRITE ===")
        print(f"[MM REWRITE] Input type: {type(response_content)}")
        print(f"[MM REWRITE] Upstream: {upstream}")
        print(f"[MM REWRITE] Original size: {len(html)} chars")

        import re

        count = 0
        patterns = [
            r'/(static/[^"\']+)',
            r'src=["\']/(static/[^"\']+?)["\']',
            r'href=["\']/(static/[^"\']+?)["\']',
            r'url\(["\']?/(static/[^"\')]+?)["\']?\)',
            r'src=["\']/(main\.[^"\']+\.js)["\']',
            r'src=["\']/(remote_entry\.[^"\']+\.js)["\']',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                count += len(matches)
            html = re.sub(pattern, f'{upstream}/\\1', html, flags=re.IGNORECASE)

        # Safety replacements
        html = html.replace('"/static/', f'"{upstream}/static/')
        html = html.replace("'/static/", f"'{upstream}/static/")
        html = html.replace('"/manifest.json', f'"{upstream}/manifest.json')
        html = html.replace("'/manifest.json", f"'{upstream}/manifest.json")

        # Strong permissive meta CSP
        csp_meta = (
            '<meta http-equiv="Content-Security-Policy" '
            'content="default-src * \'unsafe-inline\' \'unsafe-eval\' data: blob:; '
            'script-src * \'unsafe-inline\' \'unsafe-eval\'; '
            'style-src * \'unsafe-inline\'; '
            'img-src * data: blob:; '
            'connect-src *; '
            'frame-src *; frame-ancestors *;">\n'
        )
        if '<head>' in html:
            html = html.replace('<head>', '<head>' + csp_meta, 1)
        else:
            html = csp_meta + html

        print(f"[MM REWRITE] Paths rewritten: {count}")
        print(f"[MM REWRITE] Final size: {len(html)} chars")
        print(f"[MM REWRITE] === END REWRITE ===")

        return html
    def process_html_response_old(self, html_str, request, endpoint_url=None, *args, **kwargs):
        logger.info("[MattermostPassthroughHandler] Processing HTML response")

        path_info = getattr(request, 'path_info', '') or ''
        lowered_html = (html_str or '').lower()
        is_login_document = (
            '/login' in path_info or
            ('mattermost' in lowered_html and 'forgot your password' in lowered_html and 'log in to your account' in lowered_html) or
            ('id="loginId"'.lower() in lowered_html and 'id="loginPassword"'.lower() in lowered_html)
        )

        # Preserve native Mattermost login HTML rather than substituting a custom bridge.
        if is_login_document:
            logger.info('[MattermostPassthroughHandler] Preserving native login document')
            return html_str, None

        logger.info('[MattermostPassthroughHandler] Preserving native non-login HTML document')
        return html_str, None

    def rewrite_upstream_body(self, body, content_type, request, endpoint_url=None, upstream_path=None):
        """Preserve native Mattermost JSON bodies for HAR parity."""
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
            from django.conf import settings
            from dose.passthrough.credential_container import PassthroughCredentialContainer
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
            session_creds = PassthroughCredentialContainer.retrieve(request, app_name='mattermost') or {}
            session_login = session_creds.get('username') or ''
            session_password = session_creds.get('password') or ''
            if self._credential_matches_active_user(request, session_login):
                login_id = session_login
                password = session_password
            else:
                login_id = ''
                password = ''

            if not login_id:
                configured_login = (extra_config.get('mattermost_login_id') or 
                                    extra_config.get('mm_login_id') or
                                    extra_config.get('mattermost_username') or
                                    extra_config.get('mm_username') or '')
                if self._credential_matches_active_user(request, configured_login):
                    login_id = configured_login
                    password = (extra_config.get('mattermost_password') or 
                                extra_config.get('mm_password') or
                                extra_config.get('password') or
                                getattr(settings, 'POLYSAAS_APP_ADMIN_PASSWORD', 'PolySaaS2026!'))

            print(f"[MM_AUTH] password present: {bool(password)}")
            if not password:
                logger.warning("[MattermostPassthroughHandler] No active-user Mattermost password available")
                return {}

            if not login_id:
                login_id = request.user.email
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
        # Never inject on login/logout — Mattermost rejects requests with a stale session token.
        if '/api/v4/users/login' in (target_url or '') or '/api/v4/users/logout' in (target_url or ''):
            return
        # Browser-sent cookie is the freshest token (set by shim after first load)
        token = request.COOKIES.get('MMAUTHTOKEN') or request.COOKIES.get('mmauthtoken')
        if not token:
            try:
                extra_config = self._get_tenantapp_extra_config(request)
                if extra_config:
                    token = (extra_config.get('mmauthtoken') or
                             extra_config.get('mm_session_token') or
                             extra_config.get('mm_token'))
            except Exception:
                pass
        if token and 'Authorization' not in headers:
            headers['Authorization'] = f'Bearer {token}'
            _src = 'browser-cookie' if request.COOKIES.get('MMAUTHTOKEN') else 'cached'
            print(f'[MM_AUTH] Injected Authorization ({_src}, token={token[:8]}...) for {target_url}')
            try:
                parsed = urlparse(target_url or '')
                mm_origin = f'{parsed.scheme}://{parsed.netloc}' if parsed.scheme and parsed.netloc else ''
                if mm_origin:
                    self._ensure_cors_allowed(request, mm_origin, token)
            except Exception as exc:
                print(f'[MM CORS] Skipping auto-patch after auth inject: {exc}')
        elif not token:
            print(f'[MM_AUTH] NO TOKEN AVAILABLE for {target_url} — request will be unauthenticated')

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
        """Normalize known non-fatal Mattermost plugin responses for the SPA."""
        normalized_path = (upstream_path or '').split('?', 1)[0]
        if normalized_path == '/plugins/github/api/v1/connected' and resp.status_code == 501:
            body_text = ''
            try:
                body_text = (resp.content or b'').decode('utf-8', errors='ignore')
            except Exception:
                body_text = ''
            if 'this plugin is not configured' in body_text.lower():
                print('[MM RESP] Normalizing unconfigured GitHub plugin probe to disconnected=false')
                replacement = b'{"connected":false}'
                resp.status_code = 200
                resp.reason = 'OK'
                resp._content = replacement
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Content-Length'] = str(len(replacement))
        return resp

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
        from django.conf import settings
        # Prefer the fresh browser-sent cookie (set by our login bridge after a
        # successful XHR login) over any cached token. Only fall back to the
        # cached/SSO-fetched token if the browser doesn't have one yet.
        token = request.COOKIES.get('MMAUTHTOKEN') or request.COOKIES.get('mmauthtoken') or ""
        if not token:
            try:
                cookies = self.get_upstream_cookies(request) or {}
                token = cookies.get("MMAUTHTOKEN") or ""
            except Exception as exc:
                logger.warning("[MattermostPassthroughHandler] Token lookup failed: %s", exc)
        logger.info("[MM Shim] token source=%s len=%d",
                    'browser' if request.COOKIES.get('MMAUTHTOKEN') else 'server', len(token))

        login_id = ""
        password = ""
        try:
            extra = self._get_tenantapp_extra_config(request) or {}
            configured_login = (extra.get('mattermost_login_id') or
                                extra.get('mm_login_id') or
                                extra.get('mattermost_username') or
                                extra.get('mm_username') or
                                extra.get('login_id') or
                                getattr(getattr(request, 'user', None), 'email', '') or '')
            if self._credential_matches_active_user(request, configured_login):
                login_id = configured_login
                password = (extra.get('mattermost_password') or
                            extra.get('mm_password') or
                            extra.get('password') or
                            getattr(settings, 'POLYSAAS_APP_ADMIN_PASSWORD', 'PolySaaS2026!') or '')
        except Exception as exc:
            logger.warning("[MattermostPassthroughHandler] Credentials lookup failed: %s", exc)

        token_js = json.dumps(token)
        login_id_js = json.dumps(login_id)
        password_js = json.dumps(password)
        proxy_js = json.dumps(proxy_prefix)
        base_js = json.dumps(base_origin.rstrip("/"))
        team_route_js = json.dumps(f"/{self._get_team_name(request)}/channels/town-square")

        return f"""
<script data-polysaas-mattermost-shim="1">
(function() {{
    var B = {base_js};
    var PROXY = {proxy_js};
    var O = window.location.origin;
    var MMAUTHTOKEN = {token_js};
    var MM_LOGIN_ID = {login_id_js};
    var MM_PASSWORD = {password_js};
    var TEAM_ROUTE = {team_route_js};

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
        if (s.startsWith(B + '/static/')) return s;
        if (s.startsWith(PROXY + '/static/')) return B + s.slice(PROXY.length);
        if (s.startsWith(B)) {{
            var tail = s.slice(B.length);
            if (!tail.startsWith('/')) tail = '/' + tail;
            return PROXY + tail;
        }}
        if (s.startsWith(O + '/')) s = s.slice(O.length);
        else if (s.startsWith('http:') || s.startsWith('https:') || s.indexOf('//') === 0) return s;
        if (s.startsWith('static/')) return B + '/' + s;
        if (s.charAt(0) !== '/') return s;
        if (s.startsWith('/static/')) return B + s;
        if (isPolySaaSPath(s)) return s;
        return PROXY + s;
    }}

    function toUpstreamApi(s) {{
        if (typeof s !== 'string') return s;
        if (!s || s.startsWith('data:') || s.startsWith('blob:')) return s;
        if (s.indexOf('/api/v4/') === -1) return s;
        if (s.startsWith(O + PROXY + '/')) return s.slice(O.length);
        if (s.startsWith(PROXY + '/')) return s;
        if (s.startsWith(B)) {{
            var tail = s.slice(B.length);
            if (!tail.startsWith('/')) tail = '/' + tail;
            return PROXY + tail;
        }}
        if (s.startsWith(O + '/')) s = s.slice(O.length);
        else if (s.startsWith('http:') || s.startsWith('https:') || s.indexOf('//') === 0) return s;
        if (s.charAt(0) === '/' && !isPolySaaSPath(s)) return PROXY + s;
        return s;
    }}

    function recoverToTeam(reason) {{
        var target = PROXY + TEAM_ROUTE;
        console.log('[PolySaaS MM] Recovering from ' + reason + ' -> ' + target);
        window.location.replace(target);
    }}

    function toPassthroughNav(s) {{
        if (typeof s !== 'string') return s;
        if (!s || s.startsWith('data:') || s.startsWith('blob:') || s.startsWith('javascript:')) return s;
        if (s.startsWith(O + PROXY + '/')) return s;
        if (s.startsWith(PROXY + '/')) return s;
        if (s.startsWith(B)) {{
            var tail = s.slice(B.length);
            if (!tail.startsWith('/')) tail = '/' + tail;
            return O + PROXY + tail;
        }}
        if (s.startsWith(O + '/')) s = s.slice(O.length);
        else if (s.startsWith('http:') || s.startsWith('https:') || s.indexOf('//') === 0) return s;
        if (s.charAt(0) !== '/') return s;
        if (isPolySaaSPath(s)) return s;
        return PROXY + s;
    }}

    function toAssetUrl(s) {{
        if (typeof s !== 'string') return s;
        if (!s || s.startsWith('data:') || s.startsWith('blob:')) return s;
        if (s.startsWith(B)) return s;
        if (s.startsWith(PROXY + '/static/')) return B + s.slice(PROXY.length);
        if (s.startsWith(O + '/')) s = s.slice(O.length);
        else if (s.startsWith('http:') || s.startsWith('https:') || s.indexOf('//') === 0) return s;
        if (s.startsWith('static/')) return B + '/' + s;
        if (s.startsWith('/static/')) return B + s;
        return s;
    }}

    // Cookie + localStorage fallback (server-side fetch interceptor still injects MM-Auth-Token header)
    if (MMAUTHTOKEN) {{
        try {{
            localStorage.setItem('storage:MMAUTHTOKEN', JSON.stringify(MMAUTHTOKEN));
            localStorage.setItem('storage:MMAuthtokenExpiry', JSON.stringify(Date.now() + 108000000));
            localStorage.setItem('MMAUTHTOKEN', MMAUTHTOKEN);
        }} catch(_e) {{}}
        document.cookie = 'MMAUTHTOKEN=' + MMAUTHTOKEN + '; path=/; max-age=108000';
        window.MMAUTHTOKEN = MMAUTHTOKEN;
        console.log('[PolySaaS MM] Token set in localStorage, ready for app init');
    }}

    console.log('[PolySaaS MM] Shim loaded. token:', MMAUTHTOKEN ? 'yes' : 'none');

    // Intercept client-side React Router navigation to /login.
    // Mattermost SPA pushes /login when its token check fails; without this hook
    // the URL changes but no server GET fires, so our bridge never serves.
    // Forcing window.location.replace produces a real GET that hits our bridge.
    (function() {{
        var _push = history.pushState;
        var _repl = history.replaceState;
        function getPath(url) {{
            try {{
                return (typeof url === 'string') ? url : (url && url.pathname) || '';
            }} catch (e) {{ return ''; }}
        }}
        function isLoginPath(url) {{
            return /\/login(\/.*)?$/.test(getPath(url));
        }}
        function isErrorPath(url) {{
            return /\/error(\/.*)?$/.test(getPath(url));
        }}
        history.pushState = function(state, title, url) {{
            if (isLoginPath(url)) {{
                console.log('[PolySaaS MM] Intercept pushState(/login) -> hard redirect to bridge');
                window.location.replace(PROXY + '/login');
                return;
            }}
            if (isErrorPath(url)) {{
                recoverToTeam('pushState(/error)');
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
            if (isErrorPath(url)) {{
                recoverToTeam('replaceState(/error)');
                return;
            }}
            return _repl.apply(this, arguments);
        }};
    }})();

    (function() {{
        function patchLocationMethod(proto, name) {{
            if (!proto) return;
            var desc = Object.getOwnPropertyDescriptor(proto, name);
            if (!desc || typeof desc.value !== 'function') return;
            var original = desc.value;
            Object.defineProperty(proto, name, {{
                value: function(url) {{
                    var mapped = toPassthroughNav(url);
                    if (mapped !== url) console.log('[PolySaaS MM] location.' + name + ':', url, '->', mapped);
                    return original.call(this, mapped);
                }},
                configurable: true,
                enumerable: desc.enumerable,
                writable: desc.writable !== false,
            }});
        }}

        function patchLocationSetter(proto, name) {{
            if (!proto) return;
            var desc = Object.getOwnPropertyDescriptor(proto, name);
            if (!desc || typeof desc.set !== 'function') return;
            Object.defineProperty(proto, name, {{
                get: desc.get,
                set: function(value) {{
                    var mapped = typeof value === 'string' ? toPassthroughNav(value) : value;
                    if (mapped !== value) console.log('[PolySaaS MM] location.' + name + ' =', value, '->', mapped);
                    return desc.set.call(this, mapped);
                }},
                configurable: true,
                enumerable: desc.enumerable,
            }});
        }}

        try {{
            var locationProto = (window.Location && window.Location.prototype) || Object.getPrototypeOf(window.location);
            patchLocationMethod(locationProto, 'assign');
            patchLocationMethod(locationProto, 'replace');
            patchLocationSetter(locationProto, 'href');
            patchLocationSetter(locationProto, 'pathname');

            var windowProto = Object.getPrototypeOf(window);
            var windowLocationDesc = windowProto && Object.getOwnPropertyDescriptor(windowProto, 'location');
            if (windowLocationDesc && typeof windowLocationDesc.set === 'function') {{
                Object.defineProperty(windowProto, 'location', {{
                    get: windowLocationDesc.get,
                    set: function(value) {{
                        var raw = (value && typeof value === 'object' && typeof value.href === 'string') ? value.href : value;
                        var mapped = typeof raw === 'string' ? toPassthroughNav(raw) : raw;
                        if (mapped !== raw) console.log('[PolySaaS MM] window.location =', raw, '->', mapped);
                        return windowLocationDesc.set.call(this, mapped);
                    }},
                    configurable: true,
                    enumerable: windowLocationDesc.enumerable,
                }});
            }}

            var _open = window.open;
            if (typeof _open === 'function') {{
                window.open = function(url) {{
                    var mapped = toPassthroughNav(url);
                    if (mapped !== url) console.log('[PolySaaS MM] window.open:', url, '->', mapped);
                    arguments[0] = mapped;
                    return _open.apply(this, arguments);
                }};
            }}
        }} catch (e) {{
            console.warn('[PolySaaS MM] location patch failed:', e);
        }}

        document.addEventListener('click', function(event) {{
            var link = event.target && event.target.closest ? event.target.closest('a[href]') : null;
            if (!link) return;
            var href = link.getAttribute('href') || '';
            var mapped = toPassthroughNav(href);
            if (mapped === href) return;
            event.preventDefault();
            console.log('[PolySaaS MM] anchor nav:', href, '->', mapped);
            window.location.assign(mapped);
        }}, true);

        document.addEventListener('submit', function(event) {{
            var form = event.target;
            if (!form || !form.getAttribute) return;
            var action = form.getAttribute('action') || '';
            var mapped = toPassthroughNav(action);
            if (mapped === action) return;
            form.setAttribute('action', mapped);
            console.log('[PolySaaS MM] form action:', action, '->', mapped);
        }}, true);
    }})();

    if (/\/error(\/.*)?$/.test(window.location.pathname)) {{
        recoverToTeam('initial /error');
        return;
    }}

    window.__webpack_public_path__ = B + '/static/';
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
            input = toUpstreamApi(input);
        }} else if (typeof Request !== 'undefined' && input instanceof Request) {{
            var u = toUpstreamApi(input.url);
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
                return r;
            }});
        }}
        return _prom;
    }};

    var _xo = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {{
        var proxied = toUpstreamApi(url);
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
                var wsUrl = url;
                if (wsUrl.indexOf('ws://') !== 0 && wsUrl.indexOf('wss://') !== 0) {{
                    wsUrl = wsUrl.replace(/^http:/, 'ws:').replace(/^https:/, 'wss:');
                }}
                var u = new URL(wsUrl, B);
                var upstream = new URL(B);
                u.hostname = upstream.hostname;
                u.port = upstream.port;
                u.protocol = upstream.protocol === 'https:' ? 'wss:' : 'ws:';
                if (MMAUTHTOKEN && !u.searchParams.get('access_token')) {{
                    u.searchParams.set('access_token', MMAUTHTOKEN);
                }}
                url = u.toString();
                console.log('[PolySaaS Mattermost] WebSocket direct:', url);
            }} catch (e) {{ console.warn('[PolySaaS Mattermost] WebSocket rewrite:', e); }}
        }}
        var ws = protocols !== undefined ? new _WS(url, protocols) : new _WS(url);
        try {{
            ws.addEventListener('open', function() {{
                console.log('[PolySaaS Mattermost] WebSocket OPEN');
            }});
            ws.addEventListener('error', function(event) {{
                console.error('[PolySaaS Mattermost] WebSocket ERROR', event);
            }});
        }} catch (_wse) {{}}
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
                if (typeof v === 'string') v = toAssetUrl(v);
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
                value = toAssetUrl(value);
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
