"""
HubSpot passthrough — proxy app.hubspot.com inside PolySaaS admin shell.

Track A of HubSpot integration. API/OAuth for User Context Manager is separate.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import timedelta
from urllib.parse import urlparse

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from dose.passthrough.handlers.handler_base import PassthroughHandlerBase, proxy_prefix_for_trigger_endpoint
from dose.polysniffer.handlers.hubspot_bases import (
    discover_origins_from_text,
    global_entry_path,
    load_known_bases,
    load_session_landing_path,
    preferred_upstream_origin,
    remember_bases,
    remember_from_location,
    remember_landing_from_location,
    remember_landing_path,
    resolve_hubspot_browse_subpath,
    rewrite_location_through_proxy,
)

logger = logging.getLogger(__name__)

_HS_OVERLAY_VER = "2026-07-03-anti-loop-v2"

_HUBSPOT_HOST_MARKERS = ('hubspot.com', 'hubspot.net')

_HUBSPOT_GLOBAL_ENTRY = "/login/"

_BYPASS_PREFIXES = (
    '/api/',
    '/hs/',
    '/hublytics/',
    '/static/',
    '/notifications/',
    '/filemanager/',
    '/webpack/',
    '/webhooks/',
)

_PORTAL_BOOTSTRAP_MARKERS = (
    '/home/v2/api/portal',
    '/home/v2/api/no-intended-portal',
)

_PORTAL_PLACEHOLDER_ID = 246571499
_HS_LOGIN_PORTAL_ID = 246571499

_PROXY_PATH_PREFIXES = (
    '/contacts/',
    '/companies/',
    '/deals/',
    '/service/',
    '/tickets/',
    '/reports/',
    '/settings/',
    '/marketing/',
    '/sales/',
    '/cms/',
    '/preferences/',
    '/home/',
    '/login/',
    '/oauth/',
    '/account/',
    '/user-guide/',
    '/notifications/',
    '/calling/',
    '/payments/',
    '/commerce/',
    '/social/',
    '/ads/',
    '/email/',
    '/automation/',
    '/workflows/',
    '/lists/',
    '/sequences/',
    '/forecasting/',
    '/dashboard/',
    '/global-home/',
    '/objects/',
)


class HubspotPassthroughHandler(PassthroughHandlerBase):
    """HubSpot web UI passthrough."""

    _DJANGO_COOKIE_NAMES = frozenset({
        'sessionid', 'csrftoken', 'messages', 'django_language',
    })

    @classmethod
    def matches_endpoint(cls, endpoint) -> bool:
        blob = ' '.join([
            str(getattr(endpoint, 'endpoint_url', '') or ''),
            str(getattr(endpoint, 'slug', '') or ''),
            str(getattr(endpoint, 'description', '') or ''),
        ]).lower()
        return 'hubspot' in blob or any(m in blob for m in _HUBSPOT_HOST_MARKERS)

    def prefers_top_level_browser(self) -> bool:
        """HubSpot SPA Browse opens top-level; home pane keeps consumers/messages."""
        return True

    def should_wrap_in_admin_template(self, request, upstream_path, **kwargs) -> bool:
        low = (upstream_path or '').lower()
        if any(low.startswith(p) for p in _BYPASS_PREFIXES):
            return False
        if self._is_static_asset(low):
            return False
        return True

    def should_process_html_response(self, request, upstream_path, **kwargs) -> bool:
        low = (upstream_path or '').lower()
        if any(low.startswith(p) for p in _BYPASS_PREFIXES):
            return False
        if self._is_static_asset(low):
            return False
        return True

    @staticmethod
    def _portal_session_key(endpoint_id: int | None) -> str:
        return f'hs_portal_id_{endpoint_id or 0}'

    @classmethod
    def _is_portal_bootstrap_path(cls, path_or_url: str) -> bool:
        low = (path_or_url or '').lower()
        path_only = low.split('?', 1)[0].rstrip('/')
        if any(marker in path_only for marker in _PORTAL_BOOTSTRAP_MARKERS):
            return True
        return path_only.endswith('/home/v2/api')

    @classmethod
    def _extract_portal_id_from_url(cls, url: str) -> int:
        raw = (url or '').strip()
        if not raw:
            return 0
        try:
            parsed = urlparse(raw if '://' in raw else f'https://app.hubspot.com{raw}')
            for key in ('portalId', 'hubId', 'portal_id', 'hub_id'):
                val = (parsed.query or '')
                for part in val.split('&'):
                    if part.lower().startswith(f'{key.lower()}='):
                        digits = part.split('=', 1)[-1].strip()
                        if digits.isdigit():
                            return int(digits)
            for seg in (parsed.path or '').split('/'):
                if seg.isdigit() and len(seg) >= 6:
                    return int(seg)
        except Exception:
            pass
        return 0

    def _remember_portal_id(self, request, endpoint_id: int | None, portal_id: int) -> None:
        if request is None or endpoint_id is None or not portal_id:
            return
        try:
            request.session[self._portal_session_key(endpoint_id)] = int(portal_id)
            request.session.modified = True
        except Exception:
            pass

    def _remember_portal_id_from_location(self, request, endpoint_id: int | None, location: str) -> None:
        pid = self._extract_portal_id_from_url(location)
        if pid:
            self._remember_portal_id(request, endpoint_id, pid)

    def _resolve_portal_id(self, request) -> int:
        svc = self._session_service(request)
        return svc.portal_id(placeholder=_PORTAL_PLACEHOLDER_ID)

    @staticmethod
    def _session_service(request, endpoint_id: int | None = None):
        from dose.services.hubspot_session import HubspotSessionService

        eid = endpoint_id
        if eid is None:
            handler = HubspotPassthroughHandler()
            eid = handler._endpoint_id(request)
        return HubspotSessionService(request, endpoint_id=eid)

    @staticmethod
    def _hubspot_client_path(request) -> str:
        client_path = getattr(request, '_polysniffer_client_path', None)
        if client_path:
            return str(client_path)
        return getattr(request, 'path_info', '') or ''

    def _build_portal_bootstrap_payload(self, request) -> tuple[bytes, str, int]:
        pid = self._resolve_portal_id(request)
        effective_pid = pid if pid else _PORTAL_PLACEHOLDER_ID
        home_path = '/home/'
        payload = json.dumps({
            'portalId': effective_pid,
            'hubId': effective_pid,
            'id': effective_pid,
            'redirectUrl': home_path,
            'nextUrl': home_path,
        })
        return payload.encode(), 'application/json', 200

    @staticmethod
    def _forward_set_cookies_from_requests_resp(src_resp, dest_response) -> None:
        try:
            for _c in src_resp.cookies:
                dest_response.cookies[_c.name] = _c.value
                dest_response.cookies[_c.name]['path'] = _c.get('path') or '/'
                dest_response.cookies[_c.name]['samesite'] = 'Lax'
        except Exception:
            pass
        try:
            raw_sc_list = []
            rh = getattr(src_resp.raw, 'headers', None)
            if rh is not None:
                if hasattr(rh, 'getlist'):
                    raw_sc_list = rh.getlist('Set-Cookie')
                elif hasattr(rh, 'items'):
                    raw_sc_list = [v for k, v in rh.items() if k.lower() == 'set-cookie']
            for sc in raw_sc_list:
                if '=' not in sc:
                    continue
                name, value = sc.split('=', 1)[0].strip(), sc.split('=', 1)[1].split(';', 1)[0].strip()
                if name and name not in dest_response.cookies:
                    dest_response.cookies[name] = value
                    dest_response.cookies[name]['path'] = '/'
                    dest_response.cookies[name]['samesite'] = 'Lax'
        except Exception:
            pass

    @staticmethod
    def _is_bad_hubspot_subpath(path: str) -> bool:
        parts = [seg.lower() for seg in (path or '').split('/') if seg]
        return any(seg in ('undefined', 'null', 'nan') for seg in parts)

    @staticmethod
    def _request_wants_portal_json(request) -> bool:
        dest = (request.META.get('HTTP_SEC_FETCH_DEST') or '').lower()
        if dest == 'document':
            return False
        if dest in ('empty', 'iframe'):
            return True
        xrw = (request.META.get('HTTP_X_REQUESTED_WITH') or '').lower()
        if xrw == 'xmlhttprequest':
            return True
        accept = (request.META.get('HTTP_ACCEPT') or '').lower()
        if accept.startswith('text/html') or (
            'text/html' in accept.split(',')[0] and 'application/json' not in accept.split(',')[0]
        ):
            return False
        if 'application/json' in accept and 'text/html' not in accept:
            return True
        return dest != 'document'

    def _redirect_to_hubspot_home(self, request, endpoint):
        endpoint_url = getattr(endpoint, 'endpoint_url', None) or 'https://app.hubspot.com'
        proxy_prefix = self._effective_proxy_prefix(request, endpoint or self.endpoint, endpoint_url)
        dest = proxy_prefix.rstrip('/') + '/home/'
        return HttpResponseRedirect(dest)

    def _respond_bad_hubspot_subpath(self, request, endpoint, sub: str):
        if self._request_wants_portal_json(request):
            body, content_type, status = self._build_portal_bootstrap_payload(request)
            logger.warning('[HubSpot] bad subpath JSON %s -> portalId bootstrap', sub)
            return HttpResponse(body, content_type=content_type, status=status)
        logger.warning('[HubSpot] bad subpath redirect %s -> home workspace', sub)
        return self._redirect_to_hubspot_home(request, endpoint)

    def _respond_portal_bootstrap(self, request, endpoint, sub: str, *, log_label: str):
        if self._request_wants_portal_json(request):
            body, content_type, status = self._build_portal_bootstrap_payload(request)
            pid = self._resolve_portal_id(request)
            logger.info('%s %s -> portalId=%s', log_label, sub, pid or _PORTAL_PLACEHOLDER_ID)
            response = HttpResponse(body, content_type=content_type, status=status)
            response['X-Frame-Options'] = 'ALLOWALL'
            response['Cache-Control'] = 'private, max-age=300'
            return response
        logger.info('%s document nav %s -> home workspace', log_label, sub)
        return self._redirect_to_hubspot_home(request, endpoint)

    def handle_request(self, request, subpath=None):
        self._bind_hubspot_request(request)
        path = (subpath or '').strip()
        if path and not path.startswith('/'):
            path = '/' + path

        # === ANTI-LOOP: only intercept genuinely malformed paths (undefined/null/nan       ===
        # segments). Do NOT match plain /home or /home/ here — that is the legitimate
        # HubSpot landing page after a successful login, and blanket-matching it caused
        # an infinite reload loop (this handler kept re-intercepting its own redirect).
        if self._is_bad_hubspot_subpath(path):
            logger.warning(f"[HubSpot] Caught bad path: {subpath} \u2192 minimal bootstrap")
            endpoint = getattr(request, '_passthrough_endpoint', None) or self.endpoint
            endpoint_url = getattr(endpoint, 'endpoint_url', None) or 'https://app.hubspot.com'
            proxy_prefix = self._effective_proxy_prefix(request, endpoint, endpoint_url)
            target = request.build_absolute_uri(proxy_prefix.rstrip('/') + '/home/')

            # Return a minimal page that forces correct path and disables bad scripts
            html = f'''<!DOCTYPE html>
<html>
<head><title>PolySaaS HubSpot Passthrough</title>
<meta http-equiv="refresh" content="0;url={target}">
<script>window.location.replace("{target}");</script>
</head>
<body><h1>Loading HubSpot...</h1></body>
</html>'''

            response = HttpResponse(html, content_type='text/html')
            response['X-Frame-Options'] = 'ALLOWALL'
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            return response

        if request.method != 'GET':
            return None

        if not self._is_portal_bootstrap_path(path):
            return None

        # Once the web session is actually validated, let this call reach the real
        # HubSpot upstream API instead of the static placeholder JSON. Serving the
        # fake stub forever after a successful login is what left /home/ stuck
        # endlessly polling a response that never changes.
        try:
            if self._session_service(request).ensure_web_cookies():
                return None
        except Exception:
            pass

        endpoint = getattr(request, '_passthrough_endpoint', None) or self.endpoint
        return self._respond_portal_bootstrap(
            request, endpoint, path, log_label='[HS PORTAL]'
        )

    def filter_cookies_for_upstream(self, request, cookies: dict) -> dict:
        filtered = {k: v for k, v in cookies.items() if k not in self._DJANGO_COOKIE_NAMES}
        if filtered.get('hubspotapi-csrf') == 'ps_local':
            filtered.pop('hubspotapi-csrf', None)
        return filtered

    def get_upstream_cookies(self, request) -> dict:
        self._bind_hubspot_request(request)
        svc = self._session_service(request)
        eid = self._endpoint_id(request)

        client_path = self._hubspot_client_path(request)
        cookies = svc.cookies_for_upstream(
            client_path=client_path,
            method=getattr(request, 'method', 'GET') or 'GET',
        )

        if not cookies:
            session_key = f'hubspot_cookies_{eid}'
            try:
                fresh = request.session.get(session_key) or {}
                if fresh:
                    logger.warning('[HubSpotHandler] Using freshly captured cookies from session (eid=%s)', eid)
                    cookies = fresh
            except Exception:
                pass
            if not cookies:
                return {}

        filtered = self.filter_cookies_for_upstream(request, cookies)
        if filtered:
            logger.warning(
                '[HubSpotHandler] Forwarding %d validated web session cookies (eid=%s)',
                len(filtered),
                eid,
            )
        return filtered

    def override_upstream_cookies(self, request, target_url: str) -> dict:
        if request.method == 'POST' and '/login' in (target_url or ''):
            eid = self._endpoint_id(request)
            session_key = f'hs_csrf_app_{eid}'
            try:
                csrf_app = request.session.get(session_key)
                if csrf_app:
                    print(f'[HubSpotHandler] Injecting csrf.app into login POST: {csrf_app[:20]}...')
                    return {'csrf.app': csrf_app}
            except Exception as exc:
                logger.warning('[HubSpotHandler] override_upstream_cookies: %s', exc)
        return {}

    def filter_query_params_for_upstream(self, request, query_params: dict) -> dict:
        self._bind_hubspot_request(request)
        if not query_params:
            return query_params
        internal_prefix = 'ps_hs_'
        filtered = {k: v for k, v in query_params.items() if not str(k).startswith(internal_prefix)}
        if len(filtered) != len(query_params):
            removed = [k for k in query_params if k not in filtered]
            print(f'[HubSpotHandler] Stripped internal query params for upstream: {removed}')
        return filtered

    def _capture_login_cookies_from_response(self, resp, request) -> None:
        eid = self._endpoint_id(request)
        captured_cookies = {}
        
        try:
            raw_sc_list = []
            rh = getattr(resp.raw, 'headers', None)
            if rh is not None:
                if hasattr(rh, 'getlist'):
                    raw_sc_list = rh.getlist('Set-Cookie')
                elif hasattr(rh, 'items'):
                    raw_sc_list = [v for k, v in rh.items() if k.lower() == 'set-cookie']
            
            try:
                for _c in resp.cookies:
                    if hasattr(_c, 'name') and hasattr(_c, 'value'):
                        captured_cookies[_c.name] = _c.value
            except Exception:
                pass
            
            cookie_names_to_capture = {
                'csrf.app', 'hubspotutk', 'hubspotulk', 'hs',
                'hubspotapi', 'hubspotapi-csrf', 'hubspotapi-prefs',
                '_fbp', '__hsmem', '__hssc', '__hssrc', '__hstc', '__hsfp'
            }
            
            for sc in raw_sc_list:
                if '=' in sc:
                    cookie_part = sc.split(';')[0]
                    name, _, value = cookie_part.partition('=')
                    name = name.strip()
                    value = value.strip()
                    if name in cookie_names_to_capture:
                        captured_cookies[name] = value
            
            if captured_cookies:
                svc = self._session_service(request, endpoint_id=eid)
                svc.persist_web_cookies(captured_cookies, source='login_post')
                logger.warning(
                    '[DIRECT LOGIN] Captured %d cookies on successful POST /login/, stored via session service (eid=%s)',
                    len(captured_cookies), eid
                )
        except Exception as e:
            logger.error('[DIRECT LOGIN] Failed to extract cookies: %s', e)

    def augment_outbound_headers(self, request, headers, target_url: str) -> None:
        if request.method == 'POST' and '/login' in (target_url or ''):
            headers['Origin'] = 'https://app.hubspot.com'
            headers['Referer'] = 'https://app.hubspot.com/login/'

        if request.method == 'GET' and '/firealarm/v4/alarm/' in (target_url or ''):
            headers['Content-Type'] = 'application/json'
            headers.pop('Content-Length', None)

        if not self._needs_bearer_auth(target_url):
            return

        try:
            token = self._session_service(request).ensure_api_token()
            headers['Authorization'] = f'Bearer {token}'
            headers['Accept'] = 'application/json, text/plain, */*'
        except Exception as exc:
            from dose.services.hubspot_api import HubspotNotConnected

            if not isinstance(exc, HubspotNotConnected):
                logger.debug('[HubSpotHandler] ensure_api_token: %s', exc)

    @staticmethod
    def _needs_bearer_auth(target_url: str) -> bool:
        target = (target_url or '').lower()
        parsed_t = urlparse(target_url or '')
        host = (parsed_t.netloc or '').lower()
        path = (parsed_t.path or '').lower()
        return (
            'api.hubapi.com' in target
            or host == 'api.hubspot.com'
            or (host.endswith('.hubspot.com') and path.startswith('/api/'))
            or path.startswith('/home/v2/api/')
        )

    def _endpoint_id(self, request) -> int | None:
        eid = getattr(request, '_polysniffer_endpoint_id', None)
        if eid is not None:
            try:
                return int(eid)
            except (TypeError, ValueError):
                pass
        endpoint = getattr(request, '_passthrough_endpoint', None) or self.endpoint
        return int(endpoint.pk) if endpoint is not None and getattr(endpoint, 'pk', None) else None

    def _effective_proxy_prefix(self, request, endpoint, endpoint_url: str | None = None) -> str:
        pub = (getattr(request, '_polysniffer_proxy_prefix', None) or '').strip()
        if pub:
            return pub.rstrip('/')
        if endpoint is not None:
            return proxy_prefix_for_trigger_endpoint(endpoint).rstrip('/')
        return self._proxy_prefix_from_url(endpoint_url or '').rstrip('/')

    def _known_bases(self, request, endpoint_url: str) -> set[str]:
        return load_known_bases(request, self._endpoint_id(request), endpoint_url or '')

    def should_follow_upstream_redirects(self, request, target_url: str, upstream_path: str) -> bool:
        return request.method != 'POST'

    def _bind_hubspot_request(self, request) -> None:
        try:
            from dose.polysniffer.handlers.hubspot_bases import bind_hubspot_passthrough_request
            bind_hubspot_passthrough_request(request)
        except Exception:
            pass
        self._seed_provisioned_hub_bases(request)

    def _seed_provisioned_hub_bases(self, request) -> None:
        if request is None:
            return
        eid = self._endpoint_id(request)
        if eid is None:
            return
        svc = self._session_service(request, endpoint_id=eid)
        if not svc.tenant_app:
            return
        extra = svc.tenant_app.extra_config or {}
        hub = (extra.get('hs_hub_subdomain') or '').strip()
        if not hub:
            return
        try:
            from dose.polysniffer.handlers.hubspot_bases import remember_bases
            remember_bases(request, eid, {f'https://{hub}'})
        except Exception:
            pass

    @staticmethod
    def _hub_subdomain_origin_from_tenant_app(ta) -> str | None:
        if not ta:
            return None
        hub = ((ta.extra_config or {}).get("hs_hub_subdomain") or "").strip()
        return f"https://{hub}" if hub else None

    def _provisioned_hub_origin(self, request) -> str | None:
        if request is None:
            return None
        tenant = getattr(request, "tenant", None)
        if tenant is None:
        try:
            from dose.utils import get_current_tenant
                tenant = get_current_tenant(request)
            except Exception:
                tenant = None
        if not tenant:
            return None
            from dose.services.hubspot_oauth import get_tenant_hubspot_app
        return self._hub_subdomain_origin_from_tenant_app(get_tenant_hubspot_app(tenant))

    def _provisioned_hub_origin_from_db(self, endpoint_id: int | None = None) -> str | None:
        req = None
        try:
            from dose.polysniffer.handlers.hubspot_bases import get_hubspot_passthrough_request
            req = get_hubspot_passthrough_request()
        except Exception:
            req = None
        if req is not None:
            prov = self._provisioned_hub_origin(req)
            if prov:
                return prov

        schema = self._active_tenant_schema(req)
        if not schema:
            return None
        from dose.tenant_app_lookup import get_tenant_app_in_schema_by_name
        ta = get_tenant_app_in_schema_by_name(schema, "hubspot")
        return self._hub_subdomain_origin_from_tenant_app(ta)

    @staticmethod
    def _active_tenant_schema(request=None) -> str | None:
        if request is not None:
            tenant = getattr(request, "tenant", None)
            if tenant is None:
                try:
                    from dose.utils import get_current_tenant
                    tenant = get_current_tenant(request)
                except Exception:
                    tenant = None
            if tenant is not None:
                schema = getattr(tenant, "schema_name", None)
                if schema and schema != "public":
                    return schema

        from django.db import connection
        try:
            with connection.cursor() as cur:
                cur.execute("SHOW search_path")
                row = cur.fetchone()
            if not row or not row[0]:
                return None
            for part in str(row[0]).split(","):
                candidate = part.strip().strip('"')
                if candidate and candidate not in ("public", "pg_catalog"):
                    return candidate
        except Exception:
            return None
        return None

    def _apply_provisioned_hub_origin(self, origin: str, endpoint_id: int | None, request=None) -> str:
        base = (origin or "").rstrip("/")
        if base != "https://app.hubspot.com":
            return base
        prov = self._provisioned_hub_origin(request) if request is not None else None
        if not prov:
            prov = self._provisioned_hub_origin_from_db(endpoint_id)
        return prov.rstrip("/") if prov else base

    def passthrough_early_shell_paths(self):
        return ("/", "/login", "/login/", "/undefined", "/undefined/", "/home")

    @classmethod
    def _sanitize_hubspot_upstream_path(cls, path: str) -> str:
        if cls._is_bad_hubspot_subpath(path):
            logger.warning('[HubSpot] sanitizing bad upstream path %s -> /home/', path)
            return '/home/'
        import re
        if re.match(r'^/home/\d+/?$', (path or '').split('?', 1)[0]):
            logger.info('[HubSpot] sanitizing portal-id home path %s -> /home/', path)
            return '/home/'
        return path

    def try_root_display_shell_response(self, request, endpoint, url_trigger_segment):
        self._bind_hubspot_request(request)
        import re

        path_only = (getattr(request, 'path_info', '') or '').split('?')[0]
        sub_match = re.match(r'^/pt/(?:admin|dose)/[^/]+(.*)$', path_only)
        sub = (sub_match.group(1) if sub_match else '') or '/'
        if not sub.startswith('/'):
            sub = '/' + sub
        if self._is_bad_hubspot_subpath(sub):
            return self._respond_bad_hubspot_subpath(request, endpoint, sub)
        if re.match(r'^/home/\d+/?$', sub.split('?', 1)[0]):
            logger.info('[HubSpot] redirect portal-id home path %s -> /home/', sub)
            return self._redirect_to_hubspot_home(request, endpoint)
        if self._is_portal_bootstrap_path(sub):
            try:
                if self._session_service(request).ensure_web_cookies():
                    return None
            except Exception:
                pass
            return self._respond_portal_bootstrap(
                request,
                endpoint,
                sub,
                log_label='[HubSpot] early-shell portal bootstrap',
            )
        sub_norm = sub.rstrip('/') or '/'
        if sub_norm not in ('/', '/login'):
            return None
        endpoint_id = self._endpoint_id(request)
        landing = load_session_landing_path(request, endpoint_id)
        if not landing:
            return None
        endpoint_url = getattr(endpoint, "endpoint_url", None) or "https://app.hubspot.com"
        proxy_prefix = self._effective_proxy_prefix(request, endpoint or self.endpoint, endpoint_url)

        dest = proxy_prefix.rstrip("/") + landing
        logger.info("[HubSpot] session landing redirect -> %s", dest)
        return HttpResponseRedirect(dest)

    def resolve_workspace_browse_subpath(self, request, endpoint) -> str:
        return resolve_hubspot_browse_subpath(request, endpoint, self._endpoint_id(request))

    def upstream_url_for_subpath(self, endpoint_url, clean_path):
        try:
            from dose.polysniffer.handlers.hubspot_bases import get_hubspot_passthrough_request
            req = get_hubspot_passthrough_request()
        except Exception:
            req = None
        if req is not None:
            self._bind_hubspot_request(req)
            self._seed_provisioned_hub_bases(req)
        endpoint_id = self._endpoint_id(req) if req else None
        if endpoint_id is None and self.endpoint is not None:
            endpoint_id = getattr(self.endpoint, "pk", None)
        if endpoint_id is None and req is not None:
            ep = getattr(req, "_passthrough_endpoint", None)
            if ep is not None and getattr(ep, "pk", None):
                endpoint_id = int(ep.pk)
                self.endpoint = ep
        origin = preferred_upstream_origin(req, endpoint_id, endpoint_url or "")
        origin = self._apply_provisioned_hub_origin(origin, endpoint_id, req)
        if not origin:
            return None
        path = clean_path if (clean_path or "").startswith("/") else f"/{clean_path or ''}"
        path = self._sanitize_hubspot_upstream_path(path)

        low = path.lower()
        if low.startswith('/home/v2/api/') or low.startswith('/firealarm/v4/alarm/'):
          return f"https://api.hubspot.com{path}"

        return f"{origin.rstrip('/')}{path}"

    def adjust_upstream_target_url(self, target_url, upstream_path=None):
        try:
            from urllib.parse import urlparse, urlunparse

            parsed = urlparse(target_url or "")
            host = (parsed.netloc or "").split(":")[0].lower()
            if host != "app.hubspot.com":
                return target_url
            req = None
            try:
                from dose.polysniffer.handlers.hubspot_bases import get_hubspot_passthrough_request
                req = get_hubspot_passthrough_request()
            except Exception:
                req = None
            if req is not None:
                self._bind_hubspot_request(req)
            eid = self._endpoint_id(req) if req else None
            if eid is None and self.endpoint is not None:
                eid = getattr(self.endpoint, "pk", None)
            if eid is None and req is not None:
                ep = getattr(req, "_passthrough_endpoint", None)
                if ep is not None and getattr(ep, "pk", None):
                    eid = int(ep.pk)
            prov = self._apply_provisioned_hub_origin("https://app.hubspot.com", eid, req)
            if not prov or prov.rstrip("/") == "https://app.hubspot.com":
                return target_url
            regional = urlparse(prov)
            return urlunparse(
                (
                    parsed.scheme or "https",
                    regional.netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )
        except Exception:
            return target_url

    @staticmethod
    def _hubspot_login_json_success(data) -> bool:
        if not isinstance(data, dict):
            return False
        err = str(data.get('error') or data.get('errorMessage') or data.get('status') or '').lower()
        if err in ('error', 'failed', 'invalid', 'unauthorized'):
            return False
        if data.get('error') or data.get('errorMessage'):
            return False
        return bool(
            data.get('redirectUrl')
            or data.get('nextUrl')
            or data.get('portalId')
            or data.get('portal')
        )

    def _hubspot_login_response_indicates_success(self, resp) -> bool:
        if resp.status_code in (301, 302, 303, 307, 308):
            return True
        if resp.status_code != 200:
            return False
        ct = (resp.headers.get('Content-Type') or '').lower()
        body = ''
        try:
            body = (resp.text or '').strip()
        except Exception:
            body = ''
        if 'json' in ct or body.startswith('{'):
            try:
                return self._hubspot_login_json_success(resp.json())
            except Exception:
                pass
        auth_markers = {'hubspotapi', 'csrf.app', 'hs', '__hsmem', 'hubspotutk'}
        try:
            names = {getattr(c, 'name', '') for c in resp.cookies}
            if auth_markers & names:
                return True
        except Exception:
            pass
        low = body.lower()
        if '<html' in low and ('sign in' in low or 'loginui' in low or 'firealarm' in low):
            return False
        return False

    def _login_success_redirect_response(self, resp, request, **context):
        endpoint_url = context.get('endpoint_url') or ''
        endpoint_id = self._endpoint_id(request)
        proxy_prefix = self._effective_proxy_prefix(
            request,
            getattr(request, '_passthrough_endpoint', None) or self.endpoint,
            endpoint_url,
        )
        try:
            self._capture_login_cookies_from_response(resp, request)
        except Exception as exc:
            logger.warning('[HubSpotHandler] login cookie capture failed: %s', exc)
        location = resp.headers.get('Location', '')
        if not location:
            try:
                data = resp.json()
                location = str(
                    data.get('redirectUrl') or data.get('nextUrl') or ''
                ).strip()
            except Exception:
                location = ''
        self._remember_portal_id_from_location(request, endpoint_id, location)
        remember_landing_path(request, endpoint_id, '/home/')
        dashboard_path = f"{proxy_prefix.rstrip('/')}/home/"
        logger.warning('[DIRECT LOGIN REDIRECT] POST /login/ success -> %s', dashboard_path)
        print(f'[HubSpotHandler] LOGIN SUCCESS: Redirecting to dashboard at {dashboard_path}')
        redirect = HttpResponse(status=302)
        redirect['Location'] = dashboard_path
        self._forward_set_cookies_from_requests_resp(resp, redirect)
        return redirect

    def postprocess_upstream_response(self, resp, request, **context):
      try:
        ct = (resp.headers.get('Content-Type') or '').lower()
        if 'text/html' in ct:
          resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
          resp.headers['Pragma'] = 'no-cache'
          resp.headers['Expires'] = '0'
      except Exception:
        pass

      upstream_path = context.get('upstream_path') or ''
      upstream_path_lower = (upstream_path or '').lower()
      if request.method == 'POST' and 'login' in upstream_path_lower:
        if self._hubspot_login_response_indicates_success(resp):
          return self._login_success_redirect_response(resp, request, **context)

      if 'login' in upstream_path.lower():
        ct = resp.headers.get('Content-Type', '?')
        loc = resp.headers.get('Location', '')
        body_preview = ''
        try:
          body_preview = resp.text[:300]
        except Exception:
          body_preview = ''
        print(f'[HubSpotHandler] LOGIN {request.method} upstream response: status={resp.status_code} ct={ct} location={loc!r}')
        print(f'[HubSpotHandler] LOGIN {request.method} body preview: {body_preview!r}')

        if request.method == 'GET' and 'login' in upstream_path.lower():
          csrf_app = None
          try:
            for _c in resp.cookies:
              if _c.name == 'csrf.app':
                csrf_app = _c.value
                break
          except Exception:
            pass

          if not csrf_app:
            raw_sc_list = []
            try:
              rh = getattr(resp.raw, 'headers', None)
              if rh is not None:
                if hasattr(rh, 'getlist'):
                  raw_sc_list = rh.getlist('Set-Cookie')
                elif hasattr(rh, 'items'):
                  raw_sc_list = [v for k, v in rh.items() if k.lower() == 'set-cookie']
            except Exception:
              pass
            for sc in raw_sc_list:
              if sc.startswith('csrf.app='):
                csrf_app = sc.split(';')[0].split('=', 1)[1].strip()
                break

          if csrf_app:
            eid = self._endpoint_id(request)
            session_key = f'hs_csrf_app_{eid}'
            try:
              request.session[session_key] = csrf_app
              print(f'[HubSpotHandler] Stored csrf.app in session (key={session_key}): {csrf_app[:20]}...')
            except Exception as _se:
              logger.warning('[HubSpotHandler] Could not store csrf.app in session: %s', _se)

        self._bind_hubspot_request(request)
        endpoint_url = context.get('endpoint_url') or ''
        endpoint_id = self._endpoint_id(request)
        proxy_prefix = self._effective_proxy_prefix(
            request,
            getattr(request, '_passthrough_endpoint', None) or self.endpoint,
            endpoint_url,
        )
        known = self._known_bases(request, endpoint_url)

        for hop in getattr(resp, 'history', None) or ():
            remember_from_location(request, endpoint_id, hop.headers.get('Location', ''))
            if hop.url:
                remember_bases(request, endpoint_id, discover_origins_from_text(hop.url))
                remember_landing_from_location(request, endpoint_id, hop.url)

        upstream_path = context.get('upstream_path') or ''
        if resp.status_code == 200 and upstream_path:
            remember_landing_path(request, endpoint_id, upstream_path)

        if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get('Location', '')
            
            remember_from_location(request, endpoint_id, location)
            self._remember_portal_id_from_location(request, endpoint_id, location)
            rewritten = rewrite_location_through_proxy(location, proxy_prefix, known)
            if rewritten != location:
                logger.info('[HubSpot] redirect %s -> %s', location, rewritten)
                redirect = HttpResponse(status=resp.status_code)
                redirect['Location'] = rewritten
                self._forward_set_cookies_from_requests_resp(resp, redirect)
                return redirect

        return resp

    def coerce_upstream_response_for_path(self, resp, request, upstream_path: str):
        if resp.status_code != 401:
            return None
        up = (upstream_path or '').lower()
        tgt = (getattr(resp, 'url', '') or '').lower()
        combined = f"{up} {tgt}"
        if not self._is_portal_bootstrap_path(combined):
            return None
        try:
            body, content_type, status = self._build_portal_bootstrap_payload(request)
            pid = self._resolve_portal_id(request)
            logger.warning(
                '[HS PORTAL COERCE] APPLY 401->%s path=%s portalId=%s effective=%s',
                status,
                up,
                pid,
                pid or _PORTAL_PLACEHOLDER_ID,
            )
            return body, content_type, status
        except Exception as exc:
            logger.debug('[HubSpotHandler] coerce_upstream_response_for_path skipped: %s', exc)
        return None

    def polysniffer_non_page_path_prefixes(self, request):
        return _BYPASS_PREFIXES

    def polysniffer_workspace_browse_subpath(self, endpoint, request=None):
        if request is not None:
            return resolve_hubspot_browse_subpath(request, endpoint, self._endpoint_id(request))
        uri = (getattr(endpoint, "starting_uri", None) or "").strip()
        if uri:
            return uri if uri.startswith("/") else f"/{uri}"
        return _HUBSPOT_GLOBAL_ENTRY

    @staticmethod
    def _canonical_host_from_bases(endpoint_url: str, known_bases: list[str] | None = None) -> str:
        regional: list[str] = []
        for origin in known_bases or []:
            parsed = urlparse(origin)
            netloc = (parsed.netloc or '').split(':')[0]
            if netloc and 'hubspot.com' in netloc.lower() and netloc.lower() != 'app.hubspot.com':
                regional.append(netloc)
        if regional:
            return sorted(regional, key=len, reverse=True)[0]
        host = urlparse((endpoint_url or "").strip()).netloc or ""
        if host and ("hubspot.com" in host.lower()):
            return host.split(":")[0]
        for origin in known_bases or []:
            parsed = urlparse(origin)
            if parsed.netloc and "hubspot.com" in parsed.netloc.lower():
                return parsed.netloc.split(":")[0]
        return "app.hubspot.com"

    def _canonical_host_for_shim(self, request, known_bases: list[str] | None) -> str:
        endpoint_url = getattr(self.endpoint, "endpoint_url", "") if self.endpoint else ""
        host = self._canonical_host_from_bases(endpoint_url, known_bases)
        if request is not None:
            prov = self._provisioned_hub_origin(request)
            if prov:
                regional = urlparse(prov).netloc.split(":")[0]
                if regional and regional.lower() != "app.hubspot.com":
                    return regional
        return host

    @staticmethod
    def _hubspot_location_spoof_iife(
        proxy_prefix: str,
        shell_prefix: str = "",
        canonical_host: str = "app.hubspot.com",
    ) -> str:
        proxy = json.dumps((proxy_prefix or "").rstrip("/"))
        shell = json.dumps((shell_prefix or "").rstrip("/"))
        host = json.dumps((canonical_host or "app.hubspot.com").split(":")[0])
        return fr"""(function() {{
  console.log('[PolySaaS HS SPOOF v5 EARLY] Running');
  var PROXY = {proxy};
  var TARGET = PROXY + '/home/';
  var PROXY_PREFIX = PROXY;
  var SHELL_PREFIX = {shell};
  var CANONICAL_HOST = {host};
  var CANONICAL_ORIGIN = 'https://' + CANONICAL_HOST;

  function killUndefined() {{
    var path = location.pathname || '';
    if (path.indexOf('/undefined') >= 0 || path.indexOf('/null') >= 0 || (path.endsWith('/home') && !path.endsWith('/home/'))) {{
      console.warn('[PolySaaS HS] KILLING bad path:', path);
      location.replace(TARGET);
      return true;
    }}
    return false;
  }}

  // Run immediately, on load, and poll
  if (killUndefined()) return;
  window.addEventListener('load', killUndefined);
  setInterval(killUndefined, 200);

  window.__PS_HUBSPOT_LOCATION_SPOOF = true;
  var _cachedRealHref = null;
  try {{
    var _proto = window.Location && window.Location.prototype;
    var _tmpDesc = _proto && Object.getOwnPropertyDescriptor(_proto, 'href');
    if (_tmpDesc && _tmpDesc.get) {{
      _cachedRealHref = _tmpDesc.get.call(window.location);
    }}
  }} catch (_ce) {{}}
  if (!_cachedRealHref) {{
    try {{ _cachedRealHref = window.location.href; }} catch (_ce2) {{}}
  }}
  var _cachedRealSearch = '';
  try {{ _cachedRealSearch = window.location.search || ''; }} catch (_crs) {{}}
  if (!window.__PS_REAL_ORIGIN) {{
    try {{
      var _proto2 = window.Location && window.Location.prototype;
      var _hostDesc = _proto2 && Object.getOwnPropertyDescriptor(_proto2, 'host');
      var _protDesc = _proto2 && Object.getOwnPropertyDescriptor(_proto2, 'protocol');
      var _realHost = (_hostDesc && _hostDesc.get) ? _hostDesc.get.call(window.location) : window.location.host;
      var _realProt = (_protDesc && _protDesc.get) ? _protDesc.get.call(window.location) : window.location.protocol;
      window.__PS_REAL_ORIGIN = _realProt + '//' + _realHost;
    }} catch (_oe) {{
      window.__PS_REAL_ORIGIN = window.location.protocol + '//' + window.location.host;
    }}
  }}
  var _realPathname = null;
  var _realHref = null;
  var _setHref = null;
  try {{
    Object.defineProperty(window, 'origin', {{
      configurable: true,
      enumerable: true,
      get: function() {{ return CANONICAL_ORIGIN; }}
    }});
  }} catch (_woe) {{}}
  function _hasBadSegment(p) {{
    var segs = (p || '').split('/');
    for (var i = 0; i < segs.length; i++) {{
      var s = segs[i].toLowerCase();
      if (s === 'undefined' || s === 'null' || s === 'nan') return true;
    }}
    return false;
  }}
  function normalizeSubpath(path) {{
    var p = path || '/';
    if (!p || p.charAt(0) !== '/') p = '/' + p;
    if (SHELL_PREFIX && p.indexOf(SHELL_PREFIX) === 0) {{
      p = p.slice(SHELL_PREFIX.length) || '/';
      if (!p || p.charAt(0) !== '/') p = '/' + p;
    }}
    var shellMatch = p.match(/^\/dose\/sniff\/\d+\/workspace(\/.*)?$/);
    if (shellMatch) {{
      p = shellMatch[1] || '/';
      if (!p || p.charAt(0) !== '/') p = '/' + p;
    }}
    if (/^\/(passthrough|native)(\/|$)/.test(p)) {{
      p = p.replace(/^\/(passthrough|native)/, '') || '/';
      if (!p || p.charAt(0) !== '/') p = '/' + p;
    }}
    if (PROXY_PREFIX && p.indexOf(PROXY_PREFIX) === 0) {{
      p = p.slice(PROXY_PREFIX.length) || '/';
    }}
    var adminMatch = p.match(/^\/pt\/admin\/[^/]+(\/.*)?$/);
    if (adminMatch) {{
      p = adminMatch[1] || '/';
    }}
    if (!p || p.charAt(0) !== '/') p = '/' + p;
    if (p.toLowerCase().indexOf('/login') === 0 && p.slice(-1) !== '/') p += '/';
    if (/^\/home\/\d+\/?$/.test(p)) p = '/home/';
    if (_hasBadSegment(p)) p = '/home/';
    return p;
  }}
  function stripInternalQueryParams(search) {{
    var s = String(search || '');
    if (!s) return '';
    try {{
      var sp = new URLSearchParams(s.charAt(0) === '?' ? s.slice(1) : s);
      sp.delete('ps_hs_popup');
      sp.delete('ps_hs_reload');
      sp.delete('ps_hs_recard');
      var out = sp.toString();
      return out ? ('?' + out) : '';
    }} catch (_siq) {{
      return s.replace(/[?&]ps_hs_(?:popup|reload|recard)=[^&]*/g, function(m, i) {{
        return i === 0 && m.charAt(0) === '?' ? '?' : '';
      }}).replace(/\?&/, '?').replace(/\?$/, '');
    }}
  }}
  function realLocationSearch() {{
    return _cachedRealSearch || '';
  }}
  function spoofedLocationSearch() {{
    return stripInternalQueryParams(realLocationSearch());
  }}
  function upstreamPathname(raw) {{
    try {{
      var actual = raw;
      if (actual == null) actual = _realPathname ? _realPathname() : (window.location.pathname || '/');
      var normalized = normalizeSubpath(actual || '/');
      if (_hasBadSegment(normalized)) normalized = '/home/';
      try {{ window.__PS_ORCH_ACTION_PATH = normalized; }} catch (_psap) {{}}
      return normalized;
    }} catch (e) {{
      var fallback = normalizeSubpath(window.location.pathname || '/');
      if (_hasBadSegment(fallback)) fallback = '/home/';
      try {{ window.__PS_ORCH_ACTION_PATH = fallback; }} catch (_psap2) {{}}
      return fallback;
    }}
  }}
  function upstreamHref(rawHref) {{
    try {{
      var actual = rawHref;
      if (actual == null) actual = _realHref ? _realHref() : (_cachedRealHref || window.location.href);
      var u = new URL(String(actual || '/'), window.__PS_REAL_ORIGIN || _cachedRealHref || window.location.href);
      u.protocol = 'https:';
      u.hostname = CANONICAL_HOST;
      u.port = '';
      u.pathname = upstreamPathname(u.pathname);
      u.search = stripInternalQueryParams(u.search || realLocationSearch());
      return u.toString();
    }} catch (e2) {{ return CANONICAL_ORIGIN + upstreamPathname(window.location.pathname || '/'); }}
  }}
  function proxyHrefFromUpstream(value) {{
    var raw = String(value || '');
    if (!raw) return raw;
    try {{
      var parsed = new URL(raw, CANONICAL_ORIGIN);
      if (parsed.hostname === CANONICAL_HOST || parsed.hostname.indexOf('app-') === 0 || parsed.hostname === 'local.hubspot.com') {{
        var subPath = normalizeSubpath(parsed.pathname || '/');
        var sub = subPath + (parsed.search || '') + (parsed.hash || '');
        if (!sub || sub.charAt(0) !== '/') sub = '/' + sub;
        var low = sub.toLowerCase();
        var isAsset = low.indexOf('/home/v2/api/') === 0 || low.indexOf('/firealarm/') === 0 ||
          low.indexOf('/hs/') === 0 || low.indexOf('/static/') === 0 || low.indexOf('/webpack/') === 0;
        if (SHELL_PREFIX && !isAsset) return SHELL_PREFIX + sub;
        if (PROXY_PREFIX) return PROXY_PREFIX + sub;
      }}
    }} catch (e3) {{}}
    return raw;
  }}
  window.__PS_GET_UPSTREAM_PATH = function() {{
    try {{ return upstreamPathname(); }} catch (_psgp) {{ return '/'; }}
  }};
  function applyHubspotLocationSpoof() {{
    try {{
      var _locProto = window.Location && window.Location.prototype;
      var _locActualProto = Object.getPrototypeOf && Object.getPrototypeOf(window.location);
      function _getDesc(prop) {{
        var d = _locProto && Object.getOwnPropertyDescriptor(_locProto, prop);
        if (!d) d = _locActualProto && Object.getOwnPropertyDescriptor(_locActualProto, prop);
        return d || null;
      }}
      var hrefDesc = _getDesc('href');
      var pathnameDesc = _getDesc('pathname');
      var hostnameDesc = _getDesc('hostname');
      var hostDesc = _getDesc('host');
      var originDesc = _getDesc('origin');
      var protocolDesc = _getDesc('protocol');
      if (!_realPathname && pathnameDesc && pathnameDesc.get) {{
        _realPathname = pathnameDesc.get.bind(window.location);
      }}
      if (!_realHref && hrefDesc && hrefDesc.get) {{
        _realHref = hrefDesc.get.bind(window.location);
      }}
      if (!_setHref && hrefDesc && hrefDesc.set) {{
        _setHref = hrefDesc.set.bind(window.location);
      }}
      if (pathnameDesc && pathnameDesc.get) {{
        var _pTarget = _locProto || _locActualProto;
        if (_pTarget) {{ try {{ Object.defineProperty(_pTarget, 'pathname', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return upstreamPathname(); }},
          set: pathnameDesc.set
        }}); }} catch(_pe) {{}} }}
      }}
      var searchDesc = _getDesc('search');
      if (searchDesc && searchDesc.get) {{
        var _sTarget = _locProto || _locActualProto;
        if (_sTarget) {{ try {{ Object.defineProperty(_sTarget, 'search', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return spoofedLocationSearch(); }},
          set: searchDesc.set
        }}); }} catch(_se) {{}} }}
      }}
      if (hostnameDesc && hostnameDesc.get) {{
        var _hnTarget = _locProto || _locActualProto;
        if (_hnTarget) {{ try {{ Object.defineProperty(_hnTarget, 'hostname', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return CANONICAL_HOST; }},
          set: hostnameDesc.set
        }}); }} catch(_hne) {{}} }}
      }}
      if (hostDesc && hostDesc.get) {{
        var _htTarget = _locProto || _locActualProto;
        if (_htTarget) {{ try {{ Object.defineProperty(_htTarget, 'host', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return CANONICAL_HOST; }},
          set: hostDesc.set
        }}); }} catch(_hte) {{}} }}
      }}
      if (originDesc && originDesc.get) {{
        var _orTarget = _locProto || _locActualProto;
        if (_orTarget) {{ try {{ Object.defineProperty(_orTarget, 'origin', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return CANONICAL_ORIGIN; }},
          set: originDesc.set
        }}); }} catch(_ore) {{}} }}
      }}
      try {{
        Object.defineProperty(window.location, 'hostname', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return CANONICAL_HOST; }}
        }});
      }} catch (_hnde) {{}}
      try {{
        Object.defineProperty(window.location, 'host', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return CANONICAL_HOST; }}
        }});
      }} catch (_hde) {{}}
      try {{
        Object.defineProperty(window.location, 'origin', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return CANONICAL_ORIGIN; }}
        }});
      }} catch (_ode) {{}}
      try {{
        Object.defineProperty(window.location, 'protocol', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return 'https:'; }}
        }});
      }} catch (_pde) {{}}
      try {{
        Object.defineProperty(window.location, 'pathname', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return upstreamPathname(); }}
        }});
      }} catch (_ptde) {{}}
      try {{
        Object.defineProperty(window.location, 'search', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return spoofedLocationSearch(); }}
        }});
      }} catch (_sde) {{}}
      if (protocolDesc && protocolDesc.get) {{
        var _prTarget = _locProto || _locActualProto;
        if (_prTarget) {{ try {{ Object.defineProperty(_prTarget, 'protocol', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return 'https:'; }},
          set: protocolDesc.set
        }}); }} catch(_pre) {{}} }}
      }}
      if (hrefDesc && hrefDesc.get && _setHref) {{
        var _hrTarget = _locProto || _locActualProto;
        if (_hrTarget) {{ try {{ Object.defineProperty(_hrTarget, 'href', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return upstreamHref(); }},
          set: function(v) {{ return _setHref(proxyHrefFromUpstream(v)); }}
        }}); }} catch(_hre) {{}} }}
        try {{ Object.defineProperty(window.location, 'href', {{
          configurable: true,
          enumerable: true,
          get: function() {{ return upstreamHref(); }},
          set: function(v) {{ return _setHref(proxyHrefFromUpstream(v)); }}
        }}); }} catch(_hre2) {{}}
      }} else {{
        try {{
          Object.defineProperty(window.location, 'href', {{
            configurable: true,
            enumerable: true,
            get: function() {{ return upstreamHref(_cachedRealHref); }},
            set: function(v) {{ window.location.assign(proxyHrefFromUpstream(String(v))); }}
          }});
        }} catch (_fb) {{}}
      }}
      if (window.Location && window.Location.prototype) {{
        try {{ window.Location.prototype.toString = function() {{ return upstreamHref(_cachedRealHref); }}; }} catch(_ts) {{}}
      }}
      try {{
        var docUrlDesc = Object.getOwnPropertyDescriptor(Document.prototype, 'URL');
        if (docUrlDesc && docUrlDesc.get) {{
          Object.defineProperty(document, 'URL', {{
            configurable: true,
            enumerable: true,
            get: function() {{ return upstreamHref(_cachedRealHref); }}
          }});
        }}
      }} catch (eDoc) {{}}
      try {{
        var docUriDesc = Object.getOwnPropertyDescriptor(Document.prototype, 'documentURI');
        if (docUriDesc && docUriDesc.get) {{
          Object.defineProperty(document, 'documentURI', {{
            configurable: true,
            enumerable: true,
            get: function() {{ return upstreamHref(_cachedRealHref); }}
          }});
        }}
      }} catch (eUri) {{}}
      try {{
        var _realLoc = window.location;
        var _spoofedLocProxy = new Proxy(_realLoc, {{
          get: function(target, prop) {{
            if (prop === 'href')     return upstreamHref(_cachedRealHref);
            if (prop === 'hostname') return CANONICAL_HOST;
            if (prop === 'host')     return CANONICAL_HOST;
            if (prop === 'origin')   return CANONICAL_ORIGIN;
            if (prop === 'protocol') return 'https:';
            if (prop === 'pathname') return upstreamPathname();
            if (prop === 'search') return spoofedLocationSearch();
            if (prop === 'toString') return function() {{ return upstreamHref(_cachedRealHref); }};
            var v = target[prop];
            return (typeof v === 'function') ? v.bind(target) : v;
          }},
          set: function(target, prop, value) {{
            if (prop === 'href') {{ target.assign(proxyHrefFromUpstream(String(value))); return true; }}
            try {{ target[prop] = value; }} catch(_sl) {{}}
            return true;
          }}
        }});
        Object.defineProperty(document, 'location', {{
          configurable: true, enumerable: true,
          get: function() {{ return _spoofedLocProxy; }},
          set: function(v) {{ window.location.assign(proxyHrefFromUpstream(String(v))); }}
        }});
        try {{
          var _docHostNow = '';
          try {{ _docHostNow = String((document.location && document.location.hostname) || ''); }} catch (_dhn) {{}}
          if (_docHostNow && _docHostNow !== CANONICAL_HOST) {{
            Object.defineProperty(Document.prototype, 'location', {{
              configurable: true,
              enumerable: true,
              get: function() {{ return _spoofedLocProxy; }},
              set: function(v) {{ window.location.assign(proxyHrefFromUpstream(String(v))); }}
            }});
          }}
        }} catch (_dlpf) {{}}
      }} catch (_prloc) {{}}
      console.log('[PolySaaS HS] location spoof', upstreamHref(_cachedRealHref), 'real=', _cachedRealHref || '?', 'hrefDesc=', !!hrefDesc, 'docLocProxy=', (function() {{ try {{ return document.location.hostname; }} catch(_) {{ return '?'; }} }}()));
    }} catch (e) {{
      console.warn('[PolySaaS HS] location spoof failed', e);
    }}
  }}
  window.__PS_HUBSPOT_REAPPLY_SPOOF = applyHubspotLocationSpoof;
  applyHubspotLocationSpoof();
  try {{
    var _formActDesc = Object.getOwnPropertyDescriptor(HTMLFormElement.prototype, 'action');
    if (_formActDesc && _formActDesc.get) {{
      Object.defineProperty(HTMLFormElement.prototype, 'action', {{
        configurable: true, enumerable: true,
        get: function() {{
          var raw = _formActDesc.get.call(this);
          try {{
            var u = new URL(raw);
            if (u.pathname.indexOf(PROXY_PREFIX) === 0) {{
              var isLoginForm = /\/login(\/|$|\?)/i.test(u.pathname);
              if (isLoginForm) {{
                u.hostname = CANONICAL_HOST;
                u.protocol = 'https:';
                u.port = '';
                u.pathname = u.pathname.slice(PROXY_PREFIX.length) || '/login/';
                return u.toString();
              }}

              u.hostname = CANONICAL_HOST;
              u.protocol = 'https:';
              u.port = '';
              u.pathname = u.pathname.slice(PROXY_PREFIX.length) || (window.location.pathname || '/');
              return u.toString();
            }}
          }} catch(_fa) {{}}
          return raw;
        }},
        set: function(v) {{ _formActDesc.set.call(this, v); }}
      }});
    }}
  }} catch (_fae) {{}}
  window.__PS_normalizeSubpath = normalizeSubpath;
}})();"""

    def polysniffer_workspace_location_spoof_script(
        self,
        proxy_prefix: str,
        shell_prefix: str = "",
        canonical_host: str = "",
    ) -> str:
        host = canonical_host or self._canonical_host_from_bases(
            getattr(self.endpoint, "endpoint_url", "") if self.endpoint else "",
        )
        body = self._hubspot_location_spoof_iife(proxy_prefix, shell_prefix, host)
        # Inject as early as possible
        return f'<script data-hubspot-location-spoof="v5-early">{body}</script>'

    def get_client_side_shim(self, proxy_prefix: str, known_bases: list[str], request=None) -> str:
        bases_js = json.dumps(known_bases)
        portal_json = ''
        if request is not None:
            try:
                body, _, _ = self._build_portal_bootstrap_payload(request)
                portal_json = body.decode('utf-8')
            except Exception:
                portal_json = ''
        if not portal_json:
            portal_json = json.dumps({
                'portalId': _PORTAL_PLACEHOLDER_ID,
                'hubId': _PORTAL_PLACEHOLDER_ID,
                'id': _PORTAL_PLACEHOLDER_ID,
                'redirectUrl': '/home/',
                'nextUrl': '/home/',
            })
        portal_json_js = json.dumps(portal_json)
        try:
            portal_id_val = int(json.loads(portal_json).get('portalId') or _PORTAL_PLACEHOLDER_ID)
        except Exception:
            portal_id_val = _PORTAL_PLACEHOLDER_ID
        portal_id_js = json.dumps(portal_id_val)
        has_valid_session = False
        if request is not None:
            try:
                has_valid_session = bool(self._session_service(request).ensure_web_cookies())
            except Exception:
                has_valid_session = False
        has_valid_session_js = json.dumps(has_valid_session)
        spoof = self._hubspot_location_spoof_iife(
            proxy_prefix=proxy_prefix,
            shell_prefix="",
            canonical_host=self._canonical_host_for_shim(request, known_bases),
        )
        return f"""
<script data-hubspot-pt-shim="1">
{spoof}
(function() {{
  var PROXY_PREFIX = {json.dumps(proxy_prefix.rstrip('/'))};
  var KNOWN_BASES = {bases_js};
  var PORTAL_BOOTSTRAP_JSON = {portal_json_js};
  var PORTAL_ID = {portal_id_js};
  // Once the real session is validated, stop faking portal-bootstrap responses so
  // HubSpot's SPA can get genuine data instead of polling a static stub forever.
  var HAS_VALID_SESSION = {has_valid_session_js};
  var normalizeSubpath = window.__PS_normalizeSubpath || function(path) {{
    var p = path || '/';
    if (!p || p.charAt(0) !== '/') p = '/' + p;
    return p;
  }};
  // NOTE: previously referenced but never defined here — every call silently threw
  // inside a try/catch and rewriteUrl() fell through to returning the URL unchanged,
  // so absolute api.hubspot.com/app.hubspot.com XHR calls never got routed through
  // our proxy and hit real CORS failures once the portal-bootstrap stub stopped
  // intercepting them post-login.
  function isAppHost(hostname) {{
    var h = String(hostname || '').toLowerCase();
    if (!h) return false;
    if (h.indexOf('hubspot.com') >= 0 || h.indexOf('hubspot.net') >= 0) return true;
    for (var i = 0; i < KNOWN_BASES.length; i++) {{
      try {{
        var kb = new URL(KNOWN_BASES[i], window.location.origin);
        if (kb.hostname && kb.hostname.toLowerCase() === h) return true;
      }} catch (_ah) {{}}
    }}
    return false;
  }}
  (function _fixBadLocationOnLoad() {{
    try {{
      var p = window.location.pathname || '';
      if (p.indexOf('/undefined') >= 0 || p.indexOf('/null/') >= 0 || p.endsWith('/null') || /\/home\/\d+\/?$/.test(p)) {{
        window.location.replace(PROXY_PREFIX + '/home/' + (window.location.search || ''));
        return;
      }}
    }} catch (_fblo) {{}}
  }})();
  try {{
    window.__hsPortalId = PORTAL_ID;
    window.hsVars = window.hsVars || {{}};
    if (!window.hsVars.portalId) window.hsVars.portalId = PORTAL_ID;
  }} catch (_pids) {{}}
  function isBadSubpathUrl(url) {{
    var s = String(url || '').toLowerCase();
    return s.indexOf('/undefined') >= 0 || s.indexOf('/null/') >= 0 || /\\/null(?:\\/|$|\\?)/.test(s);
  }}
  function isPortalBootstrapUrl(url) {{
    var s = String(url || '');
    if (s.indexOf('/home/v2/api/portal') >= 0 || s.indexOf('/home/v2/api/no-intended-portal') >= 0) return true;
    try {{
      var u = new URL(s, window.__PS_REAL_ORIGIN || window.location.origin);
      var p = (u.pathname || '').replace(/\\/+$/, '').toLowerCase();
      return p.endsWith('/home/v2/api');
    }} catch (_ipb) {{ return false; }}
  }}
  function portalBootstrapResponse() {{
    if (!PORTAL_BOOTSTRAP_JSON) return null;
    try {{
      return new Response(PORTAL_BOOTSTRAP_JSON, {{
        status: 200,
        headers: {{'Content-Type': 'application/json'}}
      }});
    }} catch (_pbr) {{ return null; }}
  }}
  function _hasCookie(name) {{
    try {{
      var raw = '; ' + (document.cookie || '');
      return raw.indexOf('; ' + String(name || '') + '=') >= 0;
    }}
    catch (_hce) {{ return false; }}
  }}
  function _browserHsAuth() {{
    try {{ return sessionStorage.getItem('ps_hs_browser_login') === '1'; }} catch (_bha) {{ return false; }}
  }}
  function _directHubspotUrl(url) {{
    if (isPortalBootstrapUrl(url)) return null;
    if (!_browserHsAuth()) return null;
    try {{
      var raw = String(url || '');
      var parsed = new URL(raw, window.__PS_REAL_ORIGIN || window.location.origin);
      if (parsed.pathname.indexOf(PROXY_PREFIX) === 0) {{
        var sub = parsed.pathname.slice(PROXY_PREFIX.length) || '/';
        if (!sub || sub.charAt(0) !== '/') sub = '/' + sub;
        for (var i = 0; i < KNOWN_BASES.length; i++) {{
          var base = KNOWN_BASES[i];
          if (base && base.indexOf('hubspot') >= 0) {{
            return base.replace(/\\/+$/, '') + sub + (parsed.search || '') + (parsed.hash || '');
          }}
        }}
        return 'https://app.hubspot.com' + sub + (parsed.search || '') + (parsed.hash || '');
      }}
      if (isAppHost(parsed.hostname) || parsed.hostname === 'api.hubspot.com') {{
        return parsed.href;
      }}
    }} catch (_dhu) {{}}
    return null;
  }}
  function rememberOrigin(origin) {{
    if (!origin || KNOWN_BASES.indexOf(origin) >= 0) return;
    if (isAppHost(origin.replace(/^https?:\\/\\//, ''))) KNOWN_BASES.push(origin);
  }}
  function isAssetPath(path) {{
    var low = (path || '').toLowerCase();
    return low.indexOf('/api/') === 0 || low.indexOf('/hs/') === 0 || low.indexOf('/static/') === 0 ||
      low.indexOf('/webpack/') === 0 || low.indexOf('/hublytics/') === 0 || low.indexOf('/notifications/') === 0;
  }}
  function workspaceNavUrl(url) {{
    var shell = window.__PS_WORKSPACE_SHELL_PREFIX || '';
    if (!shell) return url;
    try {{
      var parsed = new URL(url, window.__PS_REAL_ORIGIN || window.location.origin);
      var realOrigin = window.__PS_REAL_ORIGIN || window.location.origin;
      if (parsed.origin !== realOrigin) return url;
      if (parsed.pathname.indexOf(PROXY_PREFIX) !== 0) return url;
      var sub = parsed.pathname.slice(PROXY_PREFIX.length) || '/';
      if (!sub || sub.charAt(0) !== '/') sub = '/' + sub;
      if (isAssetPath(sub)) return url;
      return shell + sub + (parsed.search || '') + (parsed.hash || '');
    }} catch (e) {{}}
    return url;
  }}
  function rewriteUrl(url) {{
    var raw = '';
    try {{ raw = String(url || ''); }} catch (_rws) {{ raw = ''; }}
    if (!raw) return url;
    if (raw.indexOf(PROXY_PREFIX) === 0) return raw;
    try {{
      var parsed = new URL(raw, window.__PS_REAL_ORIGIN || window.location.origin);
      if (parsed.pathname.indexOf('/pt/admin/') === 0) {{
        var m = parsed.pathname.match(/^\/pt\/admin\/[^/]+(\/.*)?$/i);
        if (m) {{
          var sub = normalizeSubpath(m[1] || '/');
          return PROXY_PREFIX + sub + (parsed.search || '') + (parsed.hash || '');
        }}
      }}
      if (isAppHost(parsed.hostname)) {{
        rememberOrigin(parsed.origin);
        return PROXY_PREFIX + normalizeSubpath(parsed.pathname) + (parsed.search || '') + (parsed.hash || '');
      }}
      var realOrigin = window.__PS_REAL_ORIGIN || window.location.origin;
      if (parsed.origin === realOrigin) {{
        var path = parsed.pathname + (parsed.search || '');
        if (path.indexOf(PROXY_PREFIX) === 0) return url;
        if (path.charAt(0) === '/') {{
          var low = path.toLowerCase();
          if (low.indexOf('/admin/') !== 0 && low.indexOf('/dose/') !== 0 &&
              low.indexOf('/static/') !== 0 && low.indexOf('/media/') !== 0) {{
            var subPath = normalizeSubpath(parsed.pathname);
            return PROXY_PREFIX + subPath + (parsed.search || '') + (parsed.hash || '');
          }}
        }}
      }}
      for (var i = 0; i < KNOWN_BASES.length; i++) {{
        var base = KNOWN_BASES[i];
        if (raw.indexOf(base) === 0) {{
          return PROXY_PREFIX + raw.slice(base.length);
        }}
      }}
    }} catch (e) {{}}
    return raw;
  }}
  var _fetch = window.fetch;
  window.fetch = function(input, init) {{
    var reqUrl = '';
    if (typeof input === 'string') reqUrl = input;
    else if (input && input.url) reqUrl = input.url;
    if (isBadSubpathUrl(reqUrl) || (isPortalBootstrapUrl(reqUrl) && !HAS_VALID_SESSION)) {{
      var stub = portalBootstrapResponse();
      if (stub) return Promise.resolve(stub);
    }}
    var directUrl = _directHubspotUrl(reqUrl);
    if (directUrl) {{
      init = init || {{}};
      if (init.credentials === undefined) init.credentials = 'include';
      return _fetch.call(this, directUrl, init);
    }}
    if (typeof input === 'string') input = rewriteUrl(input);
    else if (input && input.url) {{
      var u = rewriteUrl(input.url);
      if (u !== input.url) input = new Request(u, input);
    }}
    return _fetch.call(this, input, init);
  }};
  var _open = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function(method, url) {{
    var directUrl = _directHubspotUrl(url);
    this._psUrl = directUrl || rewriteUrl(url);
    this._psDirect = !!directUrl;
    arguments[1] = this._psUrl;
    return _open.apply(this, arguments);
  }};
  var _send = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.send = function(body) {{
    if ((isBadSubpathUrl(this._psUrl || '') || (isPortalBootstrapUrl(this._psUrl || '') && !HAS_VALID_SESSION)) && PORTAL_BOOTSTRAP_JSON) {{
      var self = this;
      setTimeout(function() {{
        try {{
          Object.defineProperty(self, 'readyState', {{value: 4, configurable: true}});
          Object.defineProperty(self, 'status', {{value: 200, configurable: true}});
          Object.defineProperty(self, 'responseText', {{value: PORTAL_BOOTSTRAP_JSON, configurable: true}});
          Object.defineProperty(self, 'response', {{value: PORTAL_BOOTSTRAP_JSON, configurable: true}});
          if (typeof self.onreadystatechange === 'function') self.onreadystatechange();
          self.dispatchEvent(new Event('load'));
          self.dispatchEvent(new Event('loadend'));
        }} catch (_xse) {{}}
      }}, 0);
      return;
    }}
    return _send.apply(this, arguments);
  }};
  function navigate(url) {{
    var u = workspaceNavUrl(rewriteUrl(String(url || '')));
    if (u) window.location.assign(u);
  }}
  var _assign = window.location.assign.bind(window.location);
  var _replace = window.location.replace.bind(window.location);
  function _navigateGuarded(url) {{
    return workspaceNavUrl(rewriteUrl(String(url || '')));
  }}
  window.location.assign = function(url) {{ _assign(_navigateGuarded(url)); }};
  window.location.replace = function(url) {{ _replace(_navigateGuarded(url)); }};
  function _guardHistoryUrl(url) {{
    if (url == null || url === '') return url;
    try {{
      var parsed = new URL(String(url), window.location.href);
      var fixed = normalizeSubpath(parsed.pathname);
      if (fixed !== parsed.pathname) {{
        parsed.pathname = fixed;
        return parsed.pathname + (parsed.search || '') + (parsed.hash || '');
      }}
    }} catch (_ghu) {{}}
    return url;
  }}
  if (!window.__PS_HS_HISTORY_GUARD) {{
    window.__PS_HS_HISTORY_GUARD = true;
    try {{
      var _pushState = history.pushState.bind(history);
      var _replaceState = history.replaceState.bind(history);
      history.pushState = function(state, title, url) {{
        return _pushState(state, title, url === undefined ? url : _guardHistoryUrl(url));
      }};
      history.replaceState = function(state, title, url) {{
        return _replaceState(state, title, url === undefined ? url : _guardHistoryUrl(url));
      }};
    }} catch (_hsg) {{}}
  }}
  if (!window.__PS_PROTO_NAV_GUARD) {{
    try {{
      window.__PS_PROTO_NAV_GUARD = true;
      var _lp = window.Location && window.Location.prototype;
      if (_lp) {{
        var _nativeAssign = _lp.assign;
        var _nativeReplace = _lp.replace;
        if (typeof _nativeAssign === 'function') {{
          _lp.assign = function(url) {{
            return _nativeAssign.call(this, _navigateGuarded(url));
          }};
        }}
        if (typeof _nativeReplace === 'function') {{
          _lp.replace = function(url) {{
            return _nativeReplace.call(this, _navigateGuarded(url));
          }};
        }}
      }}
    }} catch (_hspn) {{}}
  }}
  if (!window.__PS_HUBSPOT_LOCATION_SPOOF) {{
    try {{
      var _hrefDesc = Object.getOwnPropertyDescriptor(window.Location.prototype, 'href');
      if (_hrefDesc && _hrefDesc.set) {{
        Object.defineProperty(window.location, 'href', {{
          configurable: true,
          get: function() {{ return _hrefDesc.get.call(window.location); }},
          set: function(v) {{ _hrefDesc.set.call(window.location, workspaceNavUrl(rewriteUrl(String(v)))); }}
        }});
      }}
    }} catch (e) {{}}
  }} else if (window.__PS_HUBSPOT_REAPPLY_SPOOF) {{
    window.__PS_HUBSPOT_REAPPLY_SPOOF();
  }}
  document.addEventListener('click', function(ev) {{
    var el = ev.target;
    var a = el && el.closest ? el.closest('a[href]') : null;
    if (!a) return;
    var tgt = (a.getAttribute('target') || '').toLowerCase();
    if (tgt === '_top' || tgt === '_parent') {{
      ev.preventDefault();
      navigate(a.href || a.getAttribute('href'));
    }}
  }}, true);
  document.addEventListener('submit', function(ev) {{
    var form = ev.target;
    if (!form || !form.getAttribute) return;
    var tgt = (form.getAttribute('target') || '').toLowerCase();
    if (tgt === '_top' || tgt === '_parent') {{
      form.setAttribute('target', '_self');
      if (form.action) form.action = rewriteUrl(form.action);
    }}
  }}, true);
  function _fixFormActions() {{
    var forms = document.querySelectorAll('form[action]');
    for (var _fi = 0; _fi < forms.length; _fi++) {{
      var _fa = forms[_fi].getAttribute('action') || '';
      if (_fa.indexOf(PROXY_PREFIX) === 0) {{
        forms[_fi].setAttribute('action', _fa.slice(PROXY_PREFIX.length) || '/');
      }}
    }}
  }}
  _fixFormActions();
  if (window.MutationObserver) {{
    new MutationObserver(_fixFormActions).observe(document.documentElement, {{
      subtree: true, childList: true, attributes: true, attributeFilter: ['action']
    }});
  }}
}})();
</script>
"""

    @staticmethod
    def _inject_hubspot_stylesheets_into_body(html: str) -> str:
        if not html or 'data-ps-hs-body-css="1"' in html:
            return html
        links = re.findall(
            r'<link\b[^>]*href=["\']https://static(?:2)?\.hsappstatic\.net[^"\']+\.css["\'][^>]*>',
            html,
            flags=re.IGNORECASE,
        )
        loader_css = (
            '<style data-ps-hs-loader="1">'
            '.polysaas-passthrough-scope .page svg,'
            '.polysaas-passthrough-scope svg {'
            'max-width:48px!important;max-height:48px!important;width:48px!important;height:48px!important;'
            '}'
            '.polysaas-passthrough-scope .page{display:flex;align-items:center;justify-content:center;min-height:120px;}'
            '</style>'
        )
        bundle = '<!-- data-ps-hs-body-css="1" -->' + loader_css + ''.join(dict.fromkeys(links))
        if re.search(r'(?i)<body[^>]*>', html):
            return re.sub(r'(?i)(<body[^>]*>)', lambda m: m.group(1) + bundle, html, count=1)
        return bundle + html

    @staticmethod
    def _simplified_home_panel_html(portal_id: int | None, upstream_origin: str, *, connect_url: str = '') -> str:
        """
        Static fallback for the HubSpot home landing page when the CRM API isn't
        connected (or a data fetch fails). See _build_hubspot_crm_dashboard_html for
        the live-data view used once a Private App / OAuth token is stored.

        Returns a content FRAGMENT (no <html>/<head>/<body>) — the passthrough embed
        wraps this directly into its own content column div, so a full document here
        causes nested-body layout breakage (content floats outside the column).
        """
        origin = (upstream_origin or 'https://app.hubspot.com').rstrip('/')
        pid_display = str(portal_id) if portal_id else 'unknown'
        connect_block = ''
        if connect_url:
            connect_block = (
                f'<a href="{connect_url}" target="_blank" rel="noopener" '
                'style="display:inline-block;margin-top:12px;font-size:13px;color:#0091ae;">'
                'Connect HubSpot API (Private App / OAuth)</a>'
            )
        return f"""
<div class="polysaas-hs-panel" style="display:flex;align-items:center;justify-content:center;min-height:70vh;font-family:Segoe UI,Helvetica Neue,Arial,sans-serif;background:#f5f8fa;">
  <div style="width:420px;padding:40px 36px;background:#fff;border-radius:8px;box-shadow:0 4px 24px rgba(0,0,0,.08);text-align:center;">
    <div style="font-size:22px;font-weight:700;color:#ff7a59;margin-bottom:18px;">HubSpot</div>
    <div style="font-size:16px;font-weight:600;color:#33475b;margin-bottom:8px;">Connected</div>
    <div style="font-size:13px;color:#516f90;margin-bottom:24px;">Portal ID: {pid_display}</div>
    <a href="{origin}/home/" target="_blank" rel="noopener"
       style="display:inline-block;width:100%;box-sizing:border-box;padding:12px;background:#ff7a59;color:#fff;
              text-decoration:none;border-radius:4px;font-size:15px;font-weight:600;">
      Open HubSpot Dashboard&nbsp;&#8599;
    </a>
    <p style="margin:20px 0 0;font-size:12px;color:#99acc2;line-height:1.5;">
      The embedded HubSpot dashboard view is temporarily unavailable. Use the button
      above to open your HubSpot account in a new tab.
    </p>
    {connect_block}
  </div>
</div>"""

    @staticmethod
    def _hs_dashboard_table(title: str, rows: list[dict], columns: list[tuple[str, str]]) -> str:
        """columns: list of (field_key, display_label)."""
        head_cells = ''.join(f'<th style="text-align:left;padding:8px 12px;font-size:12px;color:#516f90;border-bottom:1px solid #e5e9ee;">{label}</th>' for _key, label in columns)
        if not rows:
            body = (
                f'<tr><td colspan="{len(columns)}" '
                'style="padding:16px 12px;font-size:13px;color:#99acc2;">No records found.</td></tr>'
            )
        else:
            body_rows = []
            for row in rows:
                cells = ''.join(
                    f'<td style="padding:8px 12px;font-size:13px;color:#33475b;border-bottom:1px solid #f0f3f5;">{row.get(key) if row.get(key) not in (None, "") else "&mdash;"}</td>'
                    for key, _label in columns
                )
                body_rows.append(f'<tr>{cells}</tr>')
            body = ''.join(body_rows)
        return f"""
<div style="margin-bottom:28px;background:#fff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.06);overflow:hidden;">
  <div style="padding:14px 16px;border-bottom:1px solid #e5e9ee;font-size:14px;font-weight:600;color:#33475b;">{title}</div>
  <table style="width:100%;border-collapse:collapse;">
    <thead><tr>{head_cells}</tr></thead>
    <tbody>{body}</tbody>
  </table>
</div>"""

    def _build_hubspot_crm_dashboard_html(self, request, portal_id: int | None, upstream_origin: str) -> str:
        """
        Live HubSpot data rendered via the official CRM REST API (Private App / OAuth
        token), instead of trying to natively render HubSpot's own web app (which
        cannot bootstrap through a server-side session-cookie proxy — see notes on
        _simplified_home_panel_html / repo memory). This keeps everything inside our
        own passthrough response, so PolySniffer capture + orchestration hooks on the
        /home/ request still apply normally.
        """
        from dose.services.hubspot_api import HubspotApiService, HubspotNotConnected, HubspotApiError
        from dose.utils import get_current_tenant

        origin = (upstream_origin or 'https://app.hubspot.com').rstrip('/')
        tenant = getattr(request, 'tenant', None) or get_current_tenant(request)
        if not tenant:
            return self._simplified_home_panel_html(portal_id, origin, connect_url='/dose/hubspot/oauth/start/')

        try:
            api = HubspotApiService.for_tenant(tenant)
            contacts = api.list_contacts(limit=5)
            companies = api.list_companies(limit=5)
            deals = api.list_deals(limit=5)
            tickets = api.list_tickets(limit=5)
            tasks = api.list_tasks(limit=5)
        except HubspotNotConnected:
            return self._simplified_home_panel_html(portal_id, origin, connect_url='/dose/hubspot/oauth/start/')
        except HubspotApiError as exc:
            logger.warning('[HubSpot] CRM dashboard fetch failed: %s', exc)
            return self._simplified_home_panel_html(portal_id, origin)

        contacts_html = self._hs_dashboard_table(
            f'Contacts ({len(contacts)})', contacts,
            [('firstname', 'First name'), ('lastname', 'Last name'), ('email', 'Email'), ('phone', 'Phone')],
        )
        companies_html = self._hs_dashboard_table(
            f'Companies ({len(companies)})', companies,
            [('name', 'Name'), ('domain', 'Domain'), ('city', 'City'), ('industry', 'Industry')],
        )
        deals_html = self._hs_dashboard_table(
            f'Deals ({len(deals)})', deals,
            [('dealname', 'Deal'), ('amount', 'Amount'), ('dealstage', 'Stage'), ('closedate', 'Close date')],
        )
        tickets_html = self._hs_dashboard_table(
            f'Tickets ({len(tickets)})', tickets,
            [('subject', 'Subject'), ('hs_pipeline_stage', 'Stage'), ('hs_ticket_priority', 'Priority')],
        )
        tasks_html = self._hs_dashboard_table(
            f'Tasks ({len(tasks)})', tasks,
            [('hs_task_subject', 'Task'), ('hs_task_status', 'Status'), ('hs_task_priority', 'Priority')],
        )
        tenant_slug = (getattr(tenant, 'slug', None) or '').strip()
        tenant_logo_url = ''
        logo_field = getattr(tenant, 'logo', None)
        if logo_field and getattr(logo_field, 'name', ''):
          try:
            tenant_logo_url = (logo_field.url or '').strip()
          except Exception:
            tenant_logo_url = ''
        tenant_logo_url = (
          tenant_logo_url
          or (getattr(request, 'session', {}).get('tenant_logo_url', '') or '').strip()
          or '/static/img/PolySaaS-Industrial-Logo.png'
        )

        return f"""
<style>
  .polysaas-hs-dashboard .polysaas-hs-connected-heading {{
    all: unset !important;
    display: block !important;
    margin: 0 !important;
    padding: 0 !important;
    font-size: 66px !important;
    line-height: 0.95 !important;
    font-weight: 900 !important;
    letter-spacing: -0.8px !important;
    color: #1f3a56 !important;
    text-transform: none !important;
    font-family: 'Lexend Deca', Segoe UI, Helvetica Neue, Arial, sans-serif !important;
    text-shadow: 0 3px 0 rgba(255, 255, 255, 0.6) !important;
  }}
</style>
<div class="polysaas-hs-dashboard" style="background:linear-gradient(180deg,#f3f7fb 0%,#eef4f9 100%);padding:0;margin:0;font-family:'Lexend Deca',Segoe UI,Helvetica Neue,Arial,sans-serif;display:flex;height:100vh;overflow:hidden;">
  <!-- Left Pane: Main Dashboard -->
  <div class="polysaas-hs-left-pane" style="flex:0 0 50%;margin-left:10px;overflow-y:auto;overflow-x:hidden;">
    <div style="max-width:1060px;margin:0 auto;padding:26px 20px 38px;">
    <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:14px;">
      <div style="display:flex;align-items:center;justify-content:center;padding:8px 10px;background:#fff;border:1px solid #d8e2ee;border-radius:10px;box-shadow:0 1px 2px rgba(27,39,51,.06);min-width:108px;min-height:108px;">
        <img src="{tenant_logo_url}" alt="PolySaaS" style="height:96px;width:96px;display:block;object-fit:contain;">
      </div>
      <div style="color:#7a8ca0;font-size:14px;">&times;</div>
      <div style="display:flex;align-items:center;justify-content:center;padding:8px 10px;background:#fff;border:1px solid #d8e2ee;border-radius:10px;box-shadow:0 1px 2px rgba(27,39,51,.06);">
        <img src="https://upload.wikimedia.org/wikipedia/commons/3/3f/HubSpot_Logo.svg" alt="HubSpot" style="height:30px;width:auto;display:block;">
      </div>
      <div style="margin-left:auto;font-size:12px;color:#516f90;">Portal ID: {portal_id or 'unknown'}</div>
    </div>

    <div style="margin:20px 0 30px;padding:18px 24px;background:linear-gradient(135deg,rgba(34,197,94,.12) 0%,rgba(34,197,94,.05) 100%);border-left:6px solid #22c55e;border-radius:8px;">
      <h2 class="polysaas-hs-connected-heading">Connected</h2>
    </div>

    <div style="background:#fff;border:1px solid #d8e2ee;border-radius:14px;overflow:hidden;box-shadow:0 8px 24px rgba(36,52,67,.08);">
      <div style="padding:14px 24px 14px;background:radial-gradient(circle at 82% 8%,rgba(255,122,89,.15),transparent 52%),linear-gradient(130deg,#243443 0%,#33475b 65%,#3f5971 100%);">
        <div style="margin-top:2px;font-size:14px;color:#d4e1ef;max-width:760px;">PolySaaS and HubSpot are linked. Use the actions below to launch HubSpot, trigger sync operations, and surface integration events back to this page.</div>
      </div>

      <div style="padding:14px 16px 6px;background:#f9fbfd;border-top:1px solid #d8e2ee;">
        <div style="display:grid;grid-template-columns:minmax(0,1fr) 188px;gap:10px;align-items:center;padding:11px 10px;border-bottom:1px solid #e5edf5;">
          <div>
            <div style="font-size:14px;font-weight:700;color:#243443;">Open HubSpot</div>
            <div style="margin-top:2px;font-size:12px;color:#62788f;">Launch the full native HubSpot experience in a separate window.</div>
          </div>
          <div style="text-align:right;">
            <button type="button" onclick="{self._open_hubspot_split_js(origin)}" style="min-width:170px;padding:9px 12px;background:#22c55e;color:#000;border:0;border-radius:8px;cursor:pointer;font-size:12px;font-weight:700;">Open HubSpot&nbsp;&#8599;</button>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:minmax(0,1fr) 188px;gap:10px;align-items:center;padding:11px 10px;border-bottom:1px solid #e5edf5;">
          <div>
            <div style="font-size:14px;font-weight:700;color:#243443;">Open HubSpot (new tab)</div>
            <div style="margin-top:2px;font-size:12px;color:#62788f;">Open HubSpot in a standard browser tab (without split-screen sizing).</div>
          </div>
          <div style="text-align:right;">
            <button type="button" onclick="window.open('{origin}/home/','_blank','noopener')" style="min-width:170px;padding:9px 12px;background:#425b76;color:#fff;border:0;border-radius:8px;cursor:pointer;font-size:12px;font-weight:700;">Open in Tab</button>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:minmax(0,1fr) 188px;gap:10px;align-items:center;padding:11px 10px;border-bottom:1px solid #e5edf5;">
          <div>
            <div style="font-size:14px;font-weight:700;color:#243443;">Sync Contacts Now</div>
            <div style="margin-top:2px;font-size:12px;color:#62788f;">Trigger a contact sync event through the integration path and report the result to the orchestration bar.</div>
          </div>
          <div style="text-align:right;">
            <button type="button" onclick="window.__psHubspotActions && window.__psHubspotActions.triggerSampleSync()" style="min-width:170px;padding:9px 12px;background:#00a4bd;color:#fff;border:0;border-radius:8px;cursor:pointer;font-size:12px;font-weight:700;">Start Sync</button>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:minmax(0,1fr) 188px;gap:10px;align-items:center;padding:11px 10px;border-bottom:1px solid #e5edf5;">
          <div>
            <div style="font-size:14px;font-weight:700;color:#243443;">Check Latest Integration Event</div>
            <div style="margin-top:2px;font-size:12px;color:#62788f;">Pull the latest event from PolySaaS and post it to the green orchestration bar.</div>
          </div>
          <div style="text-align:right;">
            <button type="button" onclick="window.__psHubspotActions && window.__psHubspotActions.showLatestEvent()" style="min-width:170px;padding:9px 12px;background:#516f90;color:#fff;border:0;border-radius:8px;cursor:pointer;font-size:12px;font-weight:700;">Check Event</button>
          </div>
        </div>
      </div>
    </div>

    <div style="margin-top:22px;font-size:12px;color:#6a8097;font-weight:600;letter-spacing:.25px;text-transform:uppercase;">Live HubSpot Snapshot</div>
    <div style="margin-top:8px;">
      {contacts_html}
      {companies_html}
      {deals_html}
      {tickets_html}
      {tasks_html}
    </div>
  </div>
  </div>
</div>
{self._hubspot_action_helpers_script_html(tenant_slug)}
{self._orchestration_polling_script_html()}
<script>
(function() {{
  window.__psHubspotSplitPopup = null;
  function hideOrchInstructionButton() {{
    try {{
      var buttons = document.querySelectorAll('button');
      for (var i = 0; i < buttons.length; i++) {{
        if (buttons[i].textContent.indexOf('Insert Orchestration') >= 0) {{
          buttons[i].style.display = 'none';
        }}
      }}
    }} catch(_) {{}}
  }}
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', hideOrchInstructionButton);
  }} else {{
    hideOrchInstructionButton();
  }}
}})();
</script>"""

    @staticmethod
    def _open_hubspot_split_js(origin: str) -> str:
        """
        Inline onclick handler: opens real HubSpot in a genuine separate top-level
        popup window (not through proxy, direct connection). Dashboard is permanently
        set to 50% width with left margin for split-screen layout.
        """
        url = f'{origin}/home/'
        return (
            "(function(){"
            "var w=Math.round(screen.availWidth/2);"
            "var h=screen.availHeight;"
            "var x=Math.round(screen.availWidth/2);"
            "var y=0;"
            f"var p=window.open('{url}','hubspot_split','width='+w+',height='+h+',left='+x+',top='+y+',resizable,scrollbars');"
            "window.__psHubspotSplitPopup=p;"
            "var bar=window.__psOrchBarInstance;"
            "if(bar&&typeof bar.showEvent==='function'){"
            "bar.showEvent('Opening HubSpot in split-screen');"
            "}"
            "})()"
        )

    @staticmethod
    def _hubspot_action_helpers_script_html(tenant_slug: str) -> str:
        safe_slug = tenant_slug or 'olient'
        return f"""
<script>
(function() {{
  var tenantSlug = '{safe_slug}';

  function showOrchEvent(message) {{
    if (window.__psOrchBarInstance && typeof window.__psOrchBarInstance.showEvent === 'function') {{
      window.__psOrchBarInstance.showEvent(message);
    }}
  }}

  function setOrchActionPath(pathOnly) {{
    var path = pathOnly || '/contacts';
    var bar = window.__psOrchBarInstance;
    var pathEl = document.getElementById('pss-action-path');
    if (pathEl) pathEl.textContent = path;
    try {{ window.__PS_ORCH_ACTION_PATH = path; }} catch (_psp) {{}}
    if (bar && typeof bar.notifyOrchestration === 'function') {{
      bar.notifyOrchestration(path, path);
    }}
  }}

  function triggerSampleSync() {{
    setOrchActionPath('/contacts');
    showOrchEvent('Synching Contacts');
    var unique = Date.now();
    var payload = {{
      properties: {{
        email: 'demo+' + unique + '@polysaas.online',
        firstname: 'PolySaaS',
        lastname: 'Sync Demo',
        phone: '+1-555-0100'
      }}
    }};
    fetch('/dose/webhook/hubspot/' + tenantSlug + '/', {{
      method: 'POST',
      credentials: 'same-origin',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify(payload)
    }})
      .then(function(r) {{ return r.ok ? r.json() : Promise.reject(); }})
      .then(function() {{ showOrchEvent('HubSpot contacts sync submitted'); }})
      .catch(function() {{ showOrchEvent('HubSpot contact sync failed'); }});
  }}

  function showLatestEvent() {{
    fetch('/dose/api/hubspot/recent-events/', {{credentials: 'same-origin'}})
      .then(function(r) {{ return r.ok ? r.json() : null; }})
      .then(function(data) {{
        if (!data || !data.events || !data.events.length) {{
          showOrchEvent('No HubSpot events yet');
          return;
        }}
        var evt = data.events[0];
        showOrchEvent(evt.description || 'HubSpot orchestration event');
      }})
      .catch(function() {{ showOrchEvent('Could not fetch latest HubSpot event'); }});
  }}

  window.__psHubspotActions = {{
    triggerSampleSync: triggerSampleSync,
    showLatestEvent: showLatestEvent
  }};
}})();
</script>"""

    @staticmethod
    def _orchestration_polling_script_html() -> str:
        """
        Same-origin poller that calls the existing (frozen) orchestration bar's
        public `showEvent()` API whenever a new HubSpot-webhook-driven
        orchestration event (e.g. HubSpotToOdooContactSync) appears, via
        /dose/api/hubspot/recent-events/. Makes the green bar reflect real
        backend events regardless of what home-page view is being shown.
        """
        return """
<script>
(function() {
  var lastEventId = 0;
  function poll() {
    var url = '/dose/api/hubspot/recent-events/' + (lastEventId ? ('?since_id=' + lastEventId) : '');
    fetch(url, {credentials: 'same-origin'})
      .then(function(r) { return r.ok ? r.json() : null; })
      .then(function(data) {
        if (!data || !data.events || !data.events.length) return;
        var events = data.events.slice().reverse();
        events.forEach(function(evt) {
          if (evt.id > lastEventId) {
            lastEventId = evt.id;
            if (window.__psOrchBarInstance && typeof window.__psOrchBarInstance.showEvent === 'function') {
              window.__psOrchBarInstance.showEvent(evt.description || 'HubSpot orchestration event');
            }
          }
        });
      })
      .catch(function() {});
  }
  poll();
  setInterval(poll, 4000);
})();
</script>"""

    @staticmethod
    def _build_hubspot_iframe_view_html(portal_id: int | None, upstream_origin: str) -> str:
        """
        DEAD CODE — kept for reference only, DO NOT wire this back into
        process_html_response(). CONFIRMED IMPOSSIBLE 2026-07-04: HubSpot's own
        /home/ response sends a `frame-ancestors 'self' app.hubspot.com` CSP
        header, so the browser hard-blocks framing it from our origin
        ("Framing 'https://app.hubspot.com/' violates the following Content
        Security Policy directive..." in console). This is enforced by the
        browser reading HubSpot's OWN headers and cannot be bypassed from our
        proxy. See repo memory hubspot-passthrough-client-shim-notes.md.
        """
        return (
            '<div style="padding:16px">HubSpot iframe embed is retired and must not be wired. '
            'Use HTML rewrite + shim. See documentation/NO_IFRAMES_IN_DOSE.md.</div>'
            f'{HubspotPassthroughHandler._orchestration_polling_script_html()}'
        )

    def process_html_response(self, html_str, request, endpoint_url=None, **context):
        self._bind_hubspot_request(request)
        if not html_str:
            return html_str
        req_path_raw = getattr(request, 'path', '') or ''
        req_path_norm = req_path_raw.split('?', 1)[0].rstrip('/')
        is_home_landing = req_path_norm.endswith('/home')
        if is_home_landing and not self._is_popup_login_request(request):
            try:
                authenticated = bool(self._session_service(request).ensure_web_cookies())
            except Exception:
                authenticated = False
            if authenticated:
        endpoint = getattr(request, '_passthrough_endpoint', None) or self.endpoint
                endpoint_url_eff = endpoint_url or getattr(endpoint, 'endpoint_url', '') or ''
                origin = self._base_from_url(endpoint_url_eff)
                pid = self._resolve_portal_id(request)
                logger.info('[HubSpot] serving CRM API dashboard + webhook-driven orchestration polling')
                return self._build_hubspot_crm_dashboard_html(request, pid, origin)
        from dose.polysniffer.handlers.hubspot_native_sniff import _rewrite_hubspot_native_html


        endpoint = getattr(request, '_passthrough_endpoint', None) or self.endpoint
        endpoint_url = endpoint_url or getattr(endpoint, 'endpoint_url', '') or ''
        prefix = self._effective_proxy_prefix(request, endpoint, endpoint_url)
        base = self._base_from_url(endpoint_url)
        endpoint_id = self._endpoint_id(request)
        known = self._known_bases(request, endpoint_url)
        html = _rewrite_hubspot_native_html(
            html_str,
            base_origin=base,
            proxy_prefix=prefix,
            handler=self,
            known_bases=known,
            request=request,
            endpoint_id=endpoint_id,
        )
        html = self._inject_hubspot_stylesheets_into_body(html)
        if self._is_popup_login_request(request):
            canon_host = self._canonical_host_from_bases(endpoint_url, sorted(known))
            early_spoof = self.polysniffer_workspace_location_spoof_script(
                prefix, shell_prefix="", canonical_host=canon_host,
            )
            if 'data-hubspot-location-spoof="1"' not in html:
                html = re.sub(
                    r'(?i)(<head[^>]*>)',
                    lambda m: m.group(1) + early_spoof,
                    html,
                    count=1,
                )
        shim = self.get_client_side_shim(prefix, sorted(known), request=request)
        if 'data-hubspot-pt-shim="1"' not in html:
            if re.search(r'(?i)<head[^>]*>', html):
                html = re.sub(
                    r'(?i)(<head[^>]*>)',
                    lambda m: m.group(1) + shim,
                    html,
                    count=1,
                )
            else:
                html = shim + html
        user_email = getattr(getattr(request, 'user', None), 'email', '') or ''
        if user_email and '/login' in (endpoint_url or '').lower() or '/login' in html[:2000].lower():
            prepop = (
                '<script data-hs-prepop="1">'
                '(function(){'
                'var _ep=' + json.dumps(user_email) + ';'
                'function _fill(){'
                'var f=document.querySelector("input[type=email],input[name=email],input[id*=email]");'
                'if(f&&!f.value){f.value=_ep;f.dispatchEvent(new Event("input",{bubbles:true}));}'
                '}'
                'if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",_fill);}else{_fill();}'
                'new MutationObserver(_fill).observe(document.documentElement,{subtree:true,childList:true});'
                '})();</script>'
            )
            html = re.sub(r'(?i)(</body>)', lambda m: prepop + m.group(1), html, count=1)
            if '</body>' not in html.lower():
                html += prepop
        req_path = getattr(request, 'path', '') or ''
        if self._needs_connect_card(request, html, endpoint_url or '', req_path):
            eid = endpoint_id or self._endpoint_id(request)
            ws_base = f'/dose/sniff/{eid}/workspace' if eid else ''
            shell_redirect = self._get_workspace_shell_redirect_script(ws_base, prefix)
            if shell_redirect and 'data-ps-hs-workspace-redirect="1"' not in html:
                html = re.sub(r'(?i)(</head>)', lambda m: shell_redirect + m.group(1), html, count=1)
                if '</head>' not in html.lower():
                    html = shell_redirect + html
            overlay = self._get_login_overlay_script(
                prefix,
                user_email,
                upstream_origin=self._base_from_url(endpoint_url or ''),
                workspace_base=ws_base,
                oauth_url='/dose/hubspot/oauth/start/',
                endpoint_id=endpoint_id or self._endpoint_id(request),
            )
            html = re.sub(r'(?i)(</head>)', lambda m: overlay + m.group(1), html, count=1)
            if '</head>' not in html.lower():
                html = overlay + html
        if self._is_popup_login_request(request):
            handshake = self._get_popup_handshake_script(prefix, endpoint_id)
            if handshake and 'data-ps-hs-popup-handshake="1"' not in html:
                html = re.sub(r'(?i)(</head>)', lambda m: handshake + m.group(1), html, count=1)
                if '</head>' not in html.lower():
                    html = handshake + html
            html = self._strip_workspace_shell_scripts_for_popup(html)
        return html

    @staticmethod
    def _strip_workspace_shell_scripts_for_popup(html: str) -> str:
        if not html:
            return html
        html = re.sub(
            r'<script data-ps-hs-workspace-redirect="1">.*?</script>',
            '',
            html,
            count=1,
            flags=re.DOTALL | re.IGNORECASE,
        )
        html = re.sub(
            r'<script data-ps-workspace-guard="1">.*?</script>',
            '',
            html,
            count=1,
            flags=re.DOTALL | re.IGNORECASE,
        )
        return html

    @staticmethod
    def _get_direct_login_script(
        proxy_prefix: str,
        user_email: str = '',
        *,
        oauth_url: str = '/dose/hubspot/oauth/start/',
    ) -> str:
        prefix_js = json.dumps(proxy_prefix.rstrip('/'))
        email_js = json.dumps(user_email or '')
        oauth_js = json.dumps(oauth_url or '/dose/hubspot/oauth/start/')
        return f"""<script data-hs-login-overlay="1">
(function() {{
  var PROXY = {prefix_js};
  var EMAIL = {email_js};
  var OAUTH_URL = {oauth_js};
  console.log('[PS HS OVERLAY] direct-login overlay v3, PROXY=', PROXY);
  function _bootstrapLoginCsrf() {{
    console.log('[PS HS OVERLAY] bootstrapping csrf via GET', PROXY + '/login/');
    return fetch(PROXY + '/login/', {{
      method: 'GET',
      credentials: 'include',
      cache: 'no-store',
      headers: {{'Accept': 'text/html,application/json,*/*'}}
    }}).then(function(r) {{
      console.log('[PS HS OVERLAY] csrf bootstrap GET status=', r.status);
      return r;
    }}).catch(function(err) {{
      console.warn('[PS HS OVERLAY] csrf bootstrap failed:', err);
      return null;
    }});
  }}
  function _wsRoot() {{
    try {{
      var m = PROXY.match(/\/pt\/polysniff\/(\d+)/);
      if (m) return '/dose/sniff/' + m[1] + '/workspace/home/';
    }} catch(e) {{}}
    return PROXY + '/home/';
  }}
  var _waitTimer = null, _waitStart = 0;
  function _startWait() {{
    var w = document.getElementById('ps-hs-wait');
    if (!w) return;
    w.style.display = 'block';
    w.textContent = 'Contacting HubSpot\u2026';
    _waitStart = Date.now();
    _waitTimer = setInterval(function() {{
      var s = Math.floor((Date.now() - _waitStart) / 1000);
      if (w) w.textContent = s > 10 ? ('Still working (' + s + 's)\u2026') : 'Contacting HubSpot\u2026';
    }}, 1000);
  }}
  function _stopWait() {{
    if (_waitTimer) {{ clearInterval(_waitTimer); _waitTimer = null; }}
    var w = document.getElementById('ps-hs-wait');
    if (w) {{ w.style.display = 'none'; }}
  }}
  function _loginPayload(email, pwd) {{
    return JSON.stringify({{loginPortalId: {_HS_LOGIN_PORTAL_ID}, email: email, password: pwd, rememberMe: false, otp: '', loginSsoTokenResponse: null}});
  }}
  function _submit() {{
    var emailEl = document.getElementById('ps-hs-email');
    var pwdEl = document.getElementById('ps-hs-pwd');
    var errEl = document.getElementById('ps-hs-err');
    var btn = document.getElementById('ps-hs-btn');
    if (!emailEl || !pwdEl || !errEl || !btn) return;
    var email = emailEl.value.trim();
    var pwd = pwdEl.value;
    if (!email || !pwd) {{
      errEl.textContent = 'Please enter your email and password.';
      errEl.style.display = 'block';
      return;
    }}
    btn.disabled = true;
    btn.textContent = 'Signing in\u2026';
    errEl.style.display = 'none';
    _startWait();
    _bootstrapLoginCsrf().then(function() {{
      return fetch(PROXY + '/login/', {{
        method: 'POST',
        headers: {{
          'Content-Type': 'application/json',
          'Accept': 'application/json, text/html, */*',
          'X-Requested-With': 'XMLHttpRequest'
        }},
        body: _loginPayload(email, pwd),
        credentials: 'include',
        redirect: 'manual'
      }});
    }}).then(function(r) {{
      if (!r) {{
        throw new Error('Login POST did not run');
      }}
      _stopWait();
      console.log('[PS HS OVERLAY] login response type=', r.type, 'status=', r.status);
      if (r.type === 'opaqueredirect' || r.status === 0 || r.status === 302) {{
        console.log('[PS HS OVERLAY] login success — navigating to workspace');
        window.location.href = _wsRoot();
        return;
      }}
      return r.text().then(function(txt) {{
        var msg = '';
        try {{
          var j = JSON.parse(txt);
          if (j && (j.redirectUrl || j.nextUrl || j.portalId || j.portal)) {{
            console.log('[PS HS DIRECT] Login success (JSON) - redirecting to workspace:', _wsRoot());
            window.location.href = _wsRoot();
            return;
          }}
          msg = (j && (j.error || j.message || j.errorMessage)) || '';
        }} catch (e) {{
          if (r.status === 200 && txt && txt.indexOf('<html') >= 0) {{
            msg = 'Sign in failed — HubSpot returned the login page. Check email/password or try OAuth.';
          }}
        }}
        if (r.ok && !msg && r.status !== 200) {{
          window.location.href = _wsRoot();
          return;
        }}
        errEl.textContent = msg || 'Sign in failed. Please check your email and password.';
        errEl.style.display = 'block';
        btn.disabled = false;
        btn.textContent = 'Sign in';
      }});
    }}).catch(function(err) {{
      _stopWait();
      console.log('[PS HS OVERLAY] error:', err);
      errEl.textContent = 'Network error \u2014 please try again.';
      errEl.style.display = 'block';
      btn.disabled = false;
      btn.textContent = 'Sign in';
    }});
  }}
  function _mount() {{
    if (document.getElementById('ps-hs-ov')) return;
    var container = document.getElementById('passthrough-inline') || document.body;
    if (container !== document.body) container.style.position = 'relative';
    var ov = document.createElement('div');
    ov.id = 'ps-hs-ov';
    ov.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;z-index:9999;display:flex;align-items:center;justify-content:center;background:#f5f8fa;font-family:Lexend Deca,Helvetica Neue,Arial,sans-serif;pointer-events:all';
    var emailVal = EMAIL.replace(/"/g, '&quot;');
    ov.innerHTML = '<div style="width:380px;padding:40px 36px;background:#fff;border-radius:8px;box-shadow:0 4px 24px rgba(0,0,0,.12);box-sizing:border-box">'
      + '<div style="text-align:center;margin-bottom:28px"><span style="font-size:26px;font-weight:700;color:#ff7a59">HubSpot</span></div>'
      + '<h2 style="margin:0 0 24px;color:#33475b;font-size:18px;font-weight:600;text-align:center">Sign in to your account</h2>'
      + '<div id="ps-hs-err" style="display:none;margin-bottom:14px;padding:10px 14px;background:#fff3f3;border-radius:4px;color:#f2545b;font-size:13px;text-align:center"></div>'
      + '<div style="margin-bottom:14px"><input id="ps-hs-email" type="email" placeholder="Email address" value="' + emailVal + '" autocomplete="email" style="width:100%;padding:11px 14px;border:1px solid #cbd6e2;border-radius:4px;font-size:15px;box-sizing:border-box;color:#33475b;outline:none"/></div>'
      + '<div style="margin-bottom:22px"><input id="ps-hs-pwd" type="password" placeholder="Password" autocomplete="current-password" style="width:100%;padding:11px 14px;border:1px solid #cbd6e2;border-radius:4px;font-size:15px;box-sizing:border-box;color:#33475b;outline:none"/></div>'
      + '<button id="ps-hs-btn" type="button" style="width:100%;padding:13px;background:#ff7a59;color:#fff;border:none;border-radius:4px;font-size:15px;font-weight:600;cursor:pointer">Sign in</button>'
      + '<p id="ps-hs-wait" style="display:none;margin:14px 0 0;text-align:center;font-size:13px;color:#516f90"></p>'
      + '<p style="margin:20px 0 0;text-align:center;font-size:12px;color:#99acc2"><a id="ps-hs-oauth" href="#" style="color:#0091ae">Connect HubSpot OAuth instead</a></p>'
      + '</div>';
    container.appendChild(ov);
    document.getElementById('ps-hs-btn').addEventListener('click', _submit);
    document.getElementById('ps-hs-oauth').addEventListener('click', function(ev) {{
      ev.preventDefault();
      window.open(OAUTH_URL, '_blank', 'noopener');
    }});
    ['ps-hs-email', 'ps-hs-pwd'].forEach(function(id) {{
      document.getElementById(id).addEventListener('keydown', function(e) {{
        if (e.key === 'Enter') _submit();
      }});
    }});
  }}
  if (document.body) {{ _mount(); }} else {{ document.addEventListener('DOMContentLoaded', _mount); }}
}})();
</script>"""

    @staticmethod
    def _is_popup_login_request(request) -> bool:
        if getattr(request, '_polysniffer_workspace_inline', False) or (getattr(request, '_polysniffer_proxy_prefix', '') or '').startswith('/pt/polysniff'):
            return False
        try:
            if (request.GET.get('ps_hs_popup') or '').strip() == '1':
                return True
        except Exception:
            pass
        return False

    def _needs_connect_card(self, request, html: str, endpoint_url: str, req_path: str = '') -> bool:
        if (getattr(request, '_polysniffer_proxy_prefix', '') or '').startswith('/pt/polysniff'):
            return False

        if self._is_popup_login_request(request):
            return False
        if self._is_login_page(html, endpoint_url, req_path):
            return True
        sample = (html or '')[:12000].lower()
        if 'login url is invalid' in sample or 'this login url is invalid' in sample:
            return True
        if 'home-redirect-ui' in sample or 'hubspot | redirecting' in sample:
            try:
                svc = self._session_service(request)
                if not svc.ensure_web_cookies():
                    return True
            except Exception:
                return True
        return False

    @staticmethod
    def _is_login_page(html: str, endpoint_url: str, req_path: str = '') -> bool:
        if '/login' in (endpoint_url or '').lower():
            return True
        if '/login' in (req_path or '').lower():
            return True
        sample = html[:4000].lower()
        if 'firealarm' in sample or 'loginui' in sample or '"login"' in sample:
            return True
        login_markers = (
            'hubspot',
            'sign in',
            'password',
            'remember me',
            'forgot password',
            'login screen for the hubspot testing environment',
        )
        hits = sum(1 for marker in login_markers if marker in sample)
        return hits >= 3

    @staticmethod
    def _get_workspace_shell_redirect_script(workspace_base: str, proxy_prefix: str) -> str:
        ws_js = json.dumps((workspace_base or '').rstrip('/') + '/')
        proxy_js = json.dumps((proxy_prefix or '').rstrip('/'))
        return f"""<script data-ps-hs-workspace-redirect="1">
(function() {{
  if (window.name && window.name.indexOf('ps_hubspot_login_') === 0) return;
  if (/[?&]ps_hs_popup=1(?:&|$)/.test(window.location.search || '')) return;
  if (document.getElementById('passthrough-inline')) return;
  var proxy = {proxy_js};
  var ws = {ws_js};
  if (!proxy || !ws) return;
  var path = window.location.pathname || '';
  if (path.indexOf(proxy) !== 0) return;
  if (path.indexOf('/api/sync-session') >= 0) return;
  var sub = path.slice(proxy.length).replace(/^\\/+/, '') || 'login/';
  var target = ws + sub + (window.location.search || '');
  try {{
    var cur = window.location.pathname + (window.location.search || '');
    var normTarget = target.split('?')[0].replace(/\\/+$/, '') || '/';
    var normCur = cur.split('?')[0].replace(/\\/+$/, '') || '/';
    if (normCur === normTarget) return;
  }} catch (_e) {{}}
  console.log('[PS HS] bare passthrough → workspace shell', target);
  window.location.replace(target);
}})();
</script>"""

    @staticmethod
    def _get_popup_handshake_script(proxy_prefix: str, endpoint_id: int | None) -> str:
        prefix_js = json.dumps((proxy_prefix or '').rstrip('/'))
        eid_js = json.dumps(int(endpoint_id or 0))
        return f"""<script data-ps-hs-popup-handshake="1">
(function() {{
  var PROXY = {prefix_js};
  var EID = {eid_js};
  var POPUP_NAME = 'ps_hubspot_login_' + EID;
  function _isPopupFlow() {{
    if (window.name && window.name.indexOf('ps_hubspot_login_') === 0) return true;
    if (window.name === 'hubspot_login') return true;
    try {{
      return /(?:^|[?&])ps_hs_popup=1(?:&|$)/.test(window.location.search || '');
    }} catch (e) {{ return false; }}
  }}
  if (!_isPopupFlow() || !EID) return;
  function _onHome() {{
    var path = (window.location.pathname || '').toLowerCase();
    var proxyLow = String(PROXY || '').toLowerCase();
    if (proxyLow && path.indexOf(proxyLow) === 0) {{
      path = path.slice(proxyLow.length) || '/';
    }}
    return path.indexOf('/home') === 0 || path === 'home' || path.indexOf('home/') === 0;
  }}
  function _notifyOpener(data) {{
    try {{
      if (window.opener && !window.opener.closed) {{
        window.opener.postMessage({{
          type: 'hubspot-session-ready',
          validated: !!(data && data.validated),
          count: (data && data.count) || 0
        }}, window.location.origin);
      }}
    }} catch (e) {{}}
  }}
  function _probe() {{
    return fetch(PROXY + '/api/sync-session/', {{
      method: 'POST',
      credentials: 'include',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{action: 'probe'}})
    }}).then(function(r) {{ return r.json().catch(function() {{ return {{validated: false}}; }}); }});
  }}
  var _done = false;
  function _checkSuccess() {{
    if (_done || !_onHome()) return;
    _probe().then(function(data) {{
      console.log('[PS HS POPUP] probe on home:', data);
      if (data && data.validated && (data.count > 0)) {{
        _done = true;
        _notifyOpener(data);
        setTimeout(function() {{ try {{ window.close(); }} catch (e) {{}} }}, 500);
      }}
    }}).catch(function(err) {{
      console.warn('[PS HS POPUP] probe failed:', err);
    }});
  }}
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', _checkSuccess);
  }} else {{
    _checkSuccess();
  }}
  var _ticks = 0;
  var _iv = setInterval(function() {{
    _ticks += 1;
    _checkSuccess();
    if (_done || _ticks > 90) clearInterval(_iv);
  }}, 1000);
}})();
</script>"""

    @staticmethod
    def _get_login_overlay_script(
        proxy_prefix: str,
        user_email: str = '',
        *,
        upstream_origin: str = 'https://app.hubspot.com',
        workspace_base: str = '',
        oauth_url: str = '/dose/hubspot/oauth/start/',
        endpoint_id: int | None = None,
    ) -> str:
        prefix_js = json.dumps(proxy_prefix.rstrip('/'))
        email_js = json.dumps(user_email or '')
        origin_js = json.dumps((upstream_origin or 'https://app.hubspot.com').rstrip('/'))
        ws_base_js = json.dumps((workspace_base or '').rstrip('/') + '/')
        oauth_js = json.dumps(oauth_url or '/dose/hubspot/oauth/start/')
        eid_js = json.dumps(int(endpoint_id or 0))
        return f"""<script data-hs-login-overlay="1">
(function() {{
  var OVERLAY_VER = {json.dumps(_HS_OVERLAY_VER)};
  console.log('[PS HS OVERLAY] overlay script running v' + OVERLAY_VER + ', PROXY=', {prefix_js});
  var PROXY = {prefix_js};
  var EP_ID = {eid_js};
  var EMAIL = {email_js};
  var HS_ORIGIN = {origin_js};
  var WS_BASE = {ws_base_js};
  var OAUTH_URL = {oauth_js};
  var _cur = (window.location.pathname || '/') + (window.location.search || '') + (window.location.hash || '');
  _cur = _cur.replace(/^\\/dose\\/sniff\\/\\d+\\/workspace\\/?/i, '/');
  if (PROXY && _cur.indexOf(PROXY) === 0) _cur = _cur.slice(PROXY.length) || '/';
  if (!_cur || _cur.charAt(0) !== '/') _cur = '/' + _cur;
  var TARGET_SUBPATH = _cur;
  function _mount() {{
    if (document.getElementById('ps-hs-ov')) return;
    var container = document.getElementById('passthrough-inline') || document.body;
    if (container !== document.body) {{
      container.style.position = 'relative';
    }}
    var ov = document.createElement('div');
    ov.id = 'ps-hs-ov';
    ov.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;z-index:9999;display:flex;align-items:center;justify-content:center;background:#f5f8fa;font-family:Lexend Deca,Helvetica Neue,Arial,sans-serif;pointer-events:all';
    ov.innerHTML = '<div style="width:420px;padding:48px 40px;background:#fff;border-radius:8px;box-shadow:0 4px 24px rgba(0,0,0,.12);box-sizing:border-box">'
      + '<div style="text-align:center;margin-bottom:28px"><span style="font-size:22px;font-weight:700;color:#ff7a59">HubSpot</span></div>'
      + '<h2 style="margin:0 0 12px;color:#33475b;font-size:19px;font-weight:600;text-align:center">Sign in to your account</h2>'
      + '<p style="margin:0 0 20px;color:#516f90;font-size:13px;line-height:1.45;text-align:center">HubSpot requires a browser session on <strong>hubspot.com</strong>. Passthrough proxy login cannot obtain the required <code style="font-size:12px">csrf.app</code> cookie.</p>'
      + '<div id="ps-hs-err" style="display:none;margin-bottom:12px;padding:10px;background:#fff3f3;border-radius:4px;color:#f2545b;font-size:13px;text-align:center"></div>'
      + '<div id="ps-hs-info" style="display:none;margin-bottom:12px;padding:10px;background:#e8f4fd;border-radius:4px;color:#33475b;font-size:13px;text-align:center;line-height:1.45"></div>'
      + '<div id="ps-hs-state" style="margin:0 0 12px;padding:8px 10px;background:#f0f7ff;border:1px solid #d0e6fb;border-radius:999px;color:#1f4e79;font-size:12px;font-weight:600;text-align:center;letter-spacing:.02em">Status: Ready to sign in</div>'
      + '<button id="ps-hs-popup" type="button" style="width:100%;padding:12px;background:#ff7a59;color:#fff;border:none;border-radius:4px;font-size:15px;font-weight:600;cursor:pointer;margin-bottom:10px">Sign in to HubSpot</button>'
      + '<button id="ps-hs-popup-ext" type="button" style="width:100%;padding:10px;background:#fff;color:#516f90;border:1px solid #cbd6e2;border-radius:4px;font-size:13px;font-weight:600;cursor:pointer;margin-bottom:10px">Sign in on hubspot.com (fallback)</button>'
      + '<button id="ps-hs-dash" type="button" style="display:none;width:100%;padding:12px;background:#0091ae;color:#fff;border:none;border-radius:4px;font-size:15px;font-weight:600;cursor:pointer;margin-bottom:10px">Open HubSpot dashboard</button>'
      + '<p style="margin:14px 0 0;text-align:center;font-size:12px;color:#99acc2;line-height:1.5">Primary: secure login window via PolySaaS passthrough (captures session server-side). Fallback opens hubspot.com directly.</p>'
      + '<p id="ps-hs-wait" style="display:none;margin:14px 0 0;text-align:center;font-size:13px;color:#516f90;line-height:1.45"></p>'
      + '<p style="margin:18px 0 0;text-align:center;font-size:12px;color:#99acc2;line-height:1.5">API / orchestration: <a id="ps-hs-oauth" href="#" style="color:#0091ae">Connect HubSpot OAuth</a></p>'
      + '</div>';
    container.appendChild(ov);
    fetch(HS_ORIGIN + '/login/', {{ method: 'GET', mode: 'no-cors', credentials: 'include' }}).catch(function() {{}});
    var _waitTimer = null;
    var _waitStarted = 0;
    function _clearWaitUx() {{
      if (_waitTimer) {{ clearInterval(_waitTimer); _waitTimer = null; }}
      var wEl = document.getElementById('ps-hs-wait');
      if (wEl) {{ wEl.style.display = 'none'; wEl.textContent = ''; }}
    }}
    function _startWaitUx(btn) {{
      _clearWaitUx();
      var wEl = document.getElementById('ps-hs-wait');
      if (!wEl) return;
      wEl.style.display = 'block';
      wEl.textContent = 'Contacting HubSpot\u2026';
      _waitStarted = Date.now();
      _waitTimer = setInterval(function() {{
        var secs = Math.floor((Date.now() - _waitStarted) / 1000);
        if (secs >= 90) {{
          wEl.textContent = 'Still waiting (' + secs + 's) \u2014 HubSpot login via passthrough can take up to 2 minutes. Do not refresh.';
          btn.textContent = 'Still working\u2026 (' + secs + 's)';
        }} else if (secs >= 45) {{
          wEl.textContent = 'Waiting for HubSpot (' + secs + 's) \u2014 upstream is slow; this is normal.';
          btn.textContent = 'Waiting for HubSpot\u2026';
        }} else if (secs >= 15) {{
          wEl.textContent = 'Waiting for HubSpot (~30s typical) \u2014 login POST is in flight.';
          btn.textContent = 'Waiting for HubSpot\u2026';
        }} else if (secs >= 5) {{
          wEl.textContent = 'HubSpot is processing your login\u2026';
        }}
      }}, 1000);
    }}
    function _showInfo(msg) {{
      var el = document.getElementById('ps-hs-info');
      if (!el) return;
      el.textContent = msg;
      el.style.display = 'block';
    }}
    function _nowStamp() {{
      try {{
        var d = new Date();
        var hh = String(d.getHours()).padStart(2, '0');
        var mm = String(d.getMinutes()).padStart(2, '0');
        var ss = String(d.getSeconds()).padStart(2, '0');
        return hh + ':' + mm + ':' + ss;
      }} catch (e) {{
        return '';
      }}
    }}
    function _setState(msg, mode) {{
      var el = document.getElementById('ps-hs-state');
      if (!el) return;
      var ts = _nowStamp();
      el.textContent = 'Status: ' + msg + (ts ? ' [' + ts + ']' : '');
      if (mode === 'ok') {{
        el.style.background = '#ecfdf3';
        el.style.borderColor = '#b7e4c7';
        el.style.color = '#1e5e37';
      }} else if (mode === 'warn') {{
        el.style.background = '#fff8e6';
        el.style.borderColor = '#ffe0a3';
        el.style.color = '#7a4a00';
      }} else if (mode === 'error') {{
        el.style.background = '#fff3f3';
        el.style.borderColor = '#ffd1d1';
        el.style.color = '#8a1f1f';
      }} else {{
        el.style.background = '#f0f7ff';
        el.style.borderColor = '#d0e6fb';
        el.style.color = '#1f4e79';
      }}
    }}
    try {{
      if (sessionStorage.getItem('ps_hs_browser_login') && sessionStorage.getItem('ps_hs_session_synced') === '1') {{
        document.getElementById('ps-hs-dash').style.display = 'block';
        _showInfo('HubSpot session synced. Click "Open HubSpot dashboard" when ready.');
        _setState('Session ready', 'ok');
      }}
    }} catch (_ss) {{}}
    function _endpointIdFromProxy() {{
      if (EP_ID > 0) return String(EP_ID);
      try {{
        var m = String(PROXY || '').match(/\\/pt\\/polysniff\\/(\\d+)/);
        return m && m[1] ? m[1] : '';
      }} catch (e) {{ return ''; }}
    }}
    function _popupLoginUrl() {{
      return (PROXY || '/pt/polysniff') + '/login/?ps_hs_popup=1';
    }}
    function _popupWindowName() {{
      var eid = _endpointIdFromProxy() || '0';
      return 'ps_hubspot_login_' + eid;
    }}
    function _syncAfterPopup() {{
      if (typeof window.__psSyncHubspotSession === 'function') {{
        return window.__psSyncHubspotSession();
      }}
      if (!PROXY) return Promise.resolve(null);
      return fetch(PROXY + '/api/sync-session/', {{
        method: 'POST',
        credentials: 'same-origin',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify({{action: 'after_popup'}})
      }}).then(function(r) {{ return r.json(); }}).catch(function(err) {{
        console.warn('[PS HS OVERLAY] sync after popup failed:', err);
        return null;
      }});
    }}
    function _syncOk(data) {{
      return !!(data && data.validated && (data.count > 0 || data.harvested));
    }}
    function _markSessionSynced() {{
      try {{ sessionStorage.setItem('ps_hs_session_synced', '1'); }} catch (e) {{}}
    }}
    function _landingUrl() {{
      return WS_BASE || (function() {{
        var ep = PROXY.replace(/\\/+$/, '').split('/').pop();
        return '/dose/sniff/' + ep + '/workspace/';
      }})();
    }}
    function _workspaceRoot() {{
      if (WS_BASE) return WS_BASE;
      try {{
        var m = String(PROXY || '').match(/\/pt\/polysniff\/(\d+)(?:\/|$)/);
        if (m && m[1]) return '/dose/sniff/' + m[1] + '/workspace/';
      }} catch (e) {{}}
      return _landingUrl();
    }}
    function _markBrowserLogin() {{
      try {{ sessionStorage.setItem('ps_hs_browser_login', '1'); }} catch (e) {{}}
    }}
    function _normalizeTargetSubpath(raw, isLoginEntry) {{
      if (isLoginEntry) return 'home/';
      var s = String(raw || '/');
      try {{
        if (/^https?:\/\//i.test(s)) {{
          var u = new URL(s);
          s = (u.pathname || '/') + (u.search || '') + (u.hash || '');
        }}
      }} catch (e) {{}}
      s = s.replace(/^\/pt\/polysniff\/\d+\/?/i, '');
      s = s.replace(/^\/dose\/sniff\/\d+\/workspace\/?/i, '');
      s = s.replace(/https?:\/\/[^/]+/ig, '');
      s = s.replace(/^\/+/, '');
      return s;
    }}
    function _openDashboard() {{
      _syncAfterPopup().then(function(data) {{
        if (!_syncOk(data)) {{
          _setState('Cannot open dashboard yet', 'warn');
          _showInfo('No stored HubSpot session yet. Use "Sign in to HubSpot" first, then try again.');
          console.warn('[PS HS OVERLAY] blocked dashboard open — no synced session', data);
          return;
        }}
        _markSessionSynced();
        try {{
          var ov = document.getElementById('ps-hs-ov');
          if (ov && ov.parentNode) ov.parentNode.removeChild(ov);
        }} catch (_) {{}}
        var pathOnly = (TARGET_SUBPATH || '/').split('?')[0].split('#')[0];
        var isLoginEntry = /\\/(login|oauth|signin|signup)\\/?$/i.test(pathOnly || '') ||
          /^\\/(login|oauth|signin|signup)(\\/|$)/i.test(pathOnly || '');
        var sub = _normalizeTargetSubpath(TARGET_SUBPATH || '/', isLoginEntry);
        var shell = _workspaceRoot();
        var inWorkspace = (window.location.pathname || '').indexOf(shell) === 0;
        var target = shell + (sub ? (sub.charAt(0) === '/' ? sub : '/' + sub) : '/');
        if (inWorkspace) {{
          try {{
            var tu = new URL(target, window.location.origin);
            tu.searchParams.set('ps_hs_reload', String(Date.now()));
            target = tu.pathname + (tu.search || '') + (tu.hash || '');
          }} catch (e) {{
            var sep = target.indexOf('?') >= 0 ? '&' : '?';
            target = target + sep + 'ps_hs_reload=' + Date.now();
          }}
          console.log('[PS HS OVERLAY] workspace soft-nav to:', target, 'original=', TARGET_SUBPATH);
          _setState('Opening dashboard in workspace', 'ok');
          window.location.assign(target);
          return;
        }}
        try {{
          var tu2 = new URL(target, window.location.origin);
          tu2.searchParams.set('ps_hs_reload', String(Date.now()));
          target = tu2.pathname + (tu2.search || '') + (tu2.hash || '');
        }} catch (e) {{
          var sep2 = target.indexOf('?') >= 0 ? '&' : '?';
          target = target + sep2 + 'ps_hs_reload=' + Date.now();
        }}
        console.log('[PS HS OVERLAY] opening dashboard at:', target, 'original=', TARGET_SUBPATH);
        _setState('Redirecting to dashboard', 'ok');
        window.location.assign(target);
      }});
    }}
    document.getElementById('ps-hs-oauth').addEventListener('click', function(ev) {{
      ev.preventDefault();
      window.open(OAUTH_URL, '_blank', 'noopener');
    }});
    function _onSessionSynced(data) {{
      if (!_syncOk(data)) return false;
      _markSessionSynced();
      document.getElementById('ps-hs-dash').style.display = 'block';
      _setState('Session synced — click dashboard', 'ok');
      _showInfo('HubSpot session stored on PolySaaS. Click "Open HubSpot dashboard" when ready.');
      return true;
    }}
    function _openHubspotPopup(usePassthrough) {{
      var errEl = document.getElementById('ps-hs-err');
      var btn = document.getElementById('ps-hs-popup');
      var btnExt = document.getElementById('ps-hs-popup-ext');
      errEl.style.display = 'none';
      var popupTarget = usePassthrough
        ? _popupLoginUrl()
        : (HS_ORIGIN + '/login/');
      var popupName = usePassthrough ? _popupWindowName() : 'hubspot_login';
      console.log('[PS HS OVERLAY] opening popup v' + OVERLAY_VER + ' at:', popupTarget);
      var popup = window.open(popupTarget, popupName, 'width=520,height=720,resizable=yes,scrollbars=yes');
      if (!popup) {{
        errEl.textContent = 'Popup blocked \u2014 allow popups for this site, or use Open in new tab from the workspace toolbar.';
        errEl.style.display = 'block';
        _setState('Popup blocked', 'error');
        return;
      }}
      window.__ps_hs_popup_flow_done = false;
      window.__ps_hs_overlay_owns_popup = true;
      btn.disabled = true;
      if (btnExt) btnExt.disabled = true;
      btn.textContent = 'Waiting for HubSpot login\u2026';
      _setState('Popup opened, waiting for sign-in', 'warn');
      _showInfo(usePassthrough
        ? 'Sign in inside the popup. When HubSpot home loads, the window will close and your session syncs to PolySaaS.'
        : 'Sign in on hubspot.com, then close the popup. Session sync may not work until cookie bridge is complete.');
      function _finishPopupFlow() {{
        if (window.__ps_hs_popup_flow_done) return;
        window.__ps_hs_popup_flow_done = true;
        if (window.__ps_hs_popup_poll) {{
          clearInterval(window.__ps_hs_popup_poll);
          window.__ps_hs_popup_poll = null;
        }}
        _setState('Popup closed, syncing session', 'warn');
        btn.disabled = false;
        if (btnExt) btnExt.disabled = false;
        btn.textContent = 'Sign in to HubSpot';
        _syncAfterPopup().then(function(data) {{
          if (_onSessionSynced(data)) return;
          document.getElementById('ps-hs-dash').style.display = 'none';
          _setState('Popup closed — session not on PolySaaS', 'warn');
          _showInfo('Login did not produce a stored HubSpot session. Try again, or use Connect HubSpot OAuth for API access.');
        }}).catch(function() {{
          document.getElementById('ps-hs-dash').style.display = 'none';
          _setState('Sync failed', 'error');
          _showInfo('Could not sync after popup close. Try signing in again.');
        }});
      }}
      window.addEventListener('message', function _psHsPopupMsg(ev) {{
        try {{
          if (!ev || ev.origin !== window.location.origin) return;
          var d = ev.data;
          if (!d || d.type !== 'hubspot-session-ready') return;
          if (window.__ps_hs_popup_flow_done) return;
          console.log('[PS HS OVERLAY] handshake from popup:', d);
          if (d.validated) {{
            window.__ps_hs_popup_flow_done = true;
            if (window.__ps_hs_popup_poll) {{
              clearInterval(window.__ps_hs_popup_poll);
              window.__ps_hs_popup_poll = null;
            }}
            btn.disabled = false;
            if (btnExt) btnExt.disabled = false;
            btn.textContent = 'Sign in to HubSpot';
            _onSessionSynced(d);
            return;
          }}
        }} catch (_me) {{}}
      }});
      window.__ps_hs_popup_poll = setInterval(function() {{
        try {{
          if (popup && popup.closed) {{
            _finishPopupFlow();
          }}
        }} catch (_pe) {{
          _finishPopupFlow();
        }}
      }}, 500);
    }}
    document.getElementById('ps-hs-popup').addEventListener('click', function() {{
      _openHubspotPopup(true);
    }});
    document.getElementById('ps-hs-popup-ext').addEventListener('click', function() {{
      _openHubspotPopup(false);
    }});
    document.getElementById('ps-hs-dash').addEventListener('click', function() {{
      _openDashboard();
    }});
    function _watchLoginEscape() {{
      if (window.__ps_hs_escape_watch) return;
      window.__ps_hs_escape_watch = true;
      setInterval(function() {{
        if (document.getElementById('ps-hs-ov')) return;
        try {{
          var t = (document.body && document.body.innerText) || '';
          if (!/login url is invalid/i.test(t)) return;
          var shell = _workspaceRoot();
          var here = window.location.pathname || '';
          if (shell && here.indexOf(shell) === 0) {{
            console.log('[PS HS OVERLAY] invalid login URL detected — reload connect card');
            window.location.replace(shell + '/login/?ps_hs_recard=' + Date.now());
          }}
        }} catch (_we) {{}}
      }}, 1500);
    }}
    _watchLoginEscape();
  }}
  if (document.body) {{ _mount(); }} else {{ document.addEventListener('DOMContentLoaded', _mount); }}
}})();
</script>"""

    @staticmethod
    def _proxy_prefix_from_url(endpoint_url: str) -> str:
        if not endpoint_url:
            return '/pt/admin/app.hubspot.com/'
        host = urlparse(endpoint_url).netloc or 'app.hubspot.com'
        return f'/pt/admin/{host}/'

    @staticmethod
    def _base_from_url(endpoint_url: str) -> str:
        if not endpoint_url:
            return 'https://app.hubspot.com'
        p = urlparse(endpoint_url)
        return f'{p.scheme}://{p.netloc}'

    @staticmethod
    def _is_static_asset(path: str) -> bool:
        return bool(re.search(r'\.(js|css|map|png|jpg|jpeg|gif|svg|ico|woff2?|ttf|json)(\?|$)', path, re.I))

    def _rewrite_html(self, html: str, proxy_prefix: str, base: str) -> str:
        prefix = proxy_prefix.rstrip('/')
        bases = {base.rstrip('/')}
        if 'app.hubspot.com' in base:
            bases.add('https://app.hubspot.com')
            bases.add('http://app.hubspot.com')

        for b in bases:
            html = html.replace(f'"{b}/', f'"{prefix}/')
            html = html.replace(f"'{b}/", f"'{prefix}/")

        def _abs_repl(match):
            path = match.group(1)
            if path.startswith('//') or ':' in path[:12]:
                return match.group(0)
            if not self._should_proxy_path(path, prefix):
                return match.group(0)
            return f'"{prefix}{path}"'

        html = re.sub(r'"(/[^"\\s#?][^"]*)"', _abs_repl, html)
        return html

    def _should_proxy_path(self, path: str, proxy_prefix: str) -> bool:
        if not path or not path.startswith('/'):
            return False
        if path.startswith(proxy_prefix):
            return False
        low = path.lower()
        if any(low.startswith(p) for p in _BYPASS_PREFIXES):
            return False
        return any(low.startswith(p) for p in _PROXY_PATH_PREFIXES) or low in ('/', '/home', '/home/')

# Register PolySniffer native sniff processor when handler module loads.
import dose.polysniffer.handlers.hubspot_native_sniff  # noqa: F401,E402