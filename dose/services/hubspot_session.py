"""
HubSpot session credentials — API (OAuth/PAT) and web UI (session cookies).

Follows the Odoo/Mattermost pattern: establish credentials server-side, then replay
on upstream requests. Web UI cookies require first-party popup sync (Track 2).
API tokens alone do not authenticate app.hubspot.com HTML.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests as http_requests

from dose.services.hubspot_api import HubspotApiService, HubspotNotConnected
from dose.services.hubspot_oauth import get_tenant_hubspot_app

logger = logging.getLogger(__name__)

DEFAULT_PLACEHOLDER_PORTAL_ID = 246571499
WEB_COOKIE_TTL_SECONDS = 7 * 24 * 3600   # 7 days — covers Playwright-provisioned sessions
WEB_VALIDATION_CACHE_SECONDS = 300
PORTAL_API_VALIDATE_URL = 'https://api.hubspot.com/home/v2/api/portal'

WEB_SESSION_COOKIE_NAMES = frozenset({
    'hubspotapi',
    'csrf.app',
    'hubspotutk',
    'hubspotulk',
    'hs',
    'hubspotapi-csrf',
    'hubspotapi-prefs',
    '__hsmem',
    '__hssc',
    '__hssrc',
    '__hstc',
    '__hsfp',
})


class HubspotSessionService:
    """Per-request HubSpot credential resolver for passthrough and API calls."""

    def __init__(self, request, *, endpoint_id: int | None = None):
        self.request = request
        self.endpoint_id = endpoint_id
        self.tenant = self._resolve_tenant(request)
        self.tenant_app = get_tenant_hubspot_app(self.tenant) if self.tenant else None

    @staticmethod
    def _resolve_tenant(request=None):
        try:
            from dose.utils import get_current_tenant

            tenant = getattr(request, 'tenant', None) if request else None
            return tenant or get_current_tenant(request)
        except Exception:
            return None

    def _extra(self) -> Dict[str, Any]:
        if not self.tenant_app:
            return {}
        cfg = self.tenant_app.extra_config
        return cfg if isinstance(cfg, dict) else {}

    def _django_session_key(self) -> str | None:
        if self.endpoint_id is None:
            return None
        return f'hubspot_cookies_{self.endpoint_id}'

    def _validation_cache_key(self) -> str | None:
        if self.endpoint_id is None:
            return None
        return f'hs_web_validated_at_{self.endpoint_id}'

    # ── Track 1: API (OAuth / Private App) ───────────────────────────────

    def has_api_connection(self) -> bool:
        return bool(self._extra().get('hs_access_token'))

    def ensure_api_token(self) -> str:
        if not self.tenant:
            raise HubspotNotConnected('No tenant context')
        if not self.tenant_app:
            raise HubspotNotConnected('HubSpot is not enabled for this tenant')
        return HubspotApiService(self.tenant, self.tenant_app)._refresh_if_needed()

    def portal_id(self, *, placeholder: int = DEFAULT_PLACEHOLDER_PORTAL_ID) -> int:
        """Real HubSpot portal/hub ID when OAuth/PAT or session landing is known."""
        if self.endpoint_id is not None:
            try:
                from dose.polysniffer.handlers.hubspot_bases import (
                    load_session_landing_path,
                )

                session_portal_key = f'hs_portal_id_{self.endpoint_id}'
                cached = self.request.session.get(session_portal_key)
                if cached is not None:
                    cached_int = int(str(cached).strip())
                    if cached_int > 0:
                        return cached_int

                landing = load_session_landing_path(self.request, self.endpoint_id)
                pid = self._extract_portal_id_from_url(landing)
                if pid:
                    return pid
            except Exception as exc:
                logger.debug('[HubspotSession] portal_id session lookup: %s', exc)

        pid_str = str(self._extra().get('hs_portal_id') or '').strip()
        if pid_str.isdigit() and int(pid_str) > 0:
            return int(pid_str)

        return int(placeholder)

    @staticmethod
    def _extract_portal_id_from_url(url: str) -> int:
        raw = (url or '').strip()
        if not raw:
            return 0
        try:
            parsed = urlparse(raw if '://' in raw else f'https://app.hubspot.com{raw}')
            for key in ('portalId', 'hubId', 'portal_id', 'hub_id'):
                for part in (parsed.query or '').split('&'):
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

    # ── Track 2: Web UI session cookies ──────────────────────────────────

    def _django_session_cookies(self) -> Dict[str, str]:
        key = self._django_session_key()
        if not key:
            return {}
        try:
            raw = self.request.session.get(key, {})
        except AttributeError:
            return {}
        if not isinstance(raw, dict):
            return {}
        return {str(k): str(v) for k, v in raw.items() if k and v}

    def _session_validation_fresh(self) -> bool:
        cache_key = self._validation_cache_key()
        if not cache_key:
            return False
        try:
            validated_at = float(self.request.session.get(cache_key) or 0)
        except (TypeError, ValueError):
            return False
        return (time.time() - validated_at) < WEB_VALIDATION_CACHE_SECONDS

    def _mark_session_validated(self) -> None:
        cache_key = self._validation_cache_key()
        if not cache_key:
            return
        try:
            self.request.session[cache_key] = time.time()
            self.request.session.modified = True
        except AttributeError:
            pass  # request has no session (management command context)

    @staticmethod
    def _cookie_header(cookies: Dict[str, str]) -> str:
        return '; '.join(f'{k}={v}' for k, v in cookies.items() if k and v)

    def validate_web_cookies(self, cookies: Dict[str, str]) -> bool:
        """Lightweight probe: portal API with session cookies (no Bearer)."""
        if not cookies:
            return False
        if not cookies.get('hubspotapi') and not cookies.get('csrf.app'):
            logger.debug('[HubspotSession] validate: missing hubspotapi/csrf.app')
            return False
        try:
            resp = http_requests.get(
                PORTAL_API_VALIDATE_URL,
                headers={
                    'Cookie': self._cookie_header(cookies),
                    'Accept': 'application/json, text/plain, */*',
                    'User-Agent': 'PolySaaS-HubSpotSession/1.0',
                },
                timeout=15,
            )
        except Exception as exc:
            logger.warning('[HubspotSession] validate request failed: %s', exc)
            return False

        if resp.status_code != 200:
            logger.warning(
                '[HubspotSession] validate failed status=%s body=%s',
                resp.status_code,
                (resp.text or '')[:200],
            )
            return False

        try:
            data = resp.json()
        except Exception:
            return False

        pid = data.get('portalId') or data.get('hubId') or data.get('id')
        if pid is not None and str(pid).strip().isdigit() and int(pid) > 0:
            logger.info('[HubspotSession] validate OK portalId=%s', pid)
            return True

        logger.warning('[HubspotSession] validate 200 but no portalId in JSON')
        return False

    def persist_web_cookies(self, cookies: Dict[str, str], *, source: str) -> None:
        """Store web session in Django session + TenantApp.extra_config (Odoo cache pattern)."""
        if not cookies:
            return

        filtered = {
            str(k): str(v)
            for k, v in cookies.items()
            if k in WEB_SESSION_COOKIE_NAMES and v
        }
        if not filtered:
            filtered = {str(k): str(v) for k, v in cookies.items() if k and v}

        key = self._django_session_key()
        if key:
            self.request.session[key] = dict(filtered)
            self.request.session.modified = True

        if self.tenant_app:
            extra = dict(self._extra())
            extra['hs_web_cookies'] = dict(filtered)
            extra['hs_web_cookies_at'] = time.time()
            extra['hs_web_cookies_source'] = source or 'unknown'
            self.tenant_app.extra_config = extra
            self.tenant_app.save(update_fields=['extra_config'])

        self._mark_session_validated()
        logger.warning(
            '[HubspotSession] persisted %d web cookies source=%s eid=%s',
            len(filtered),
            source,
            self.endpoint_id,
        )

    def clear_web_cookies(self, *, reason: str = '') -> None:
        key = self._django_session_key()
        if key and key in self.request.session:
            del self.request.session[key]
            self.request.session.modified = True
        cache_key = self._validation_cache_key()
        if cache_key and cache_key in self.request.session:
            del self.request.session[cache_key]
            self.request.session.modified = True

        if self.tenant_app:
            extra = dict(self._extra())
            extra.pop('hs_web_cookies', None)
            extra.pop('hs_web_cookies_at', None)
            extra.pop('hs_web_cookies_source', None)
            self.tenant_app.extra_config = extra
            self.tenant_app.save(update_fields=['extra_config'])

        logger.warning('[HubspotSession] cleared web cookies reason=%s eid=%s', reason, self.endpoint_id)

    def ensure_web_cookies(self) -> Dict[str, str]:
        """
        Return validated web session cookies for app.hubspot.com upstream requests.
        Priority: Django session → TenantApp cache (TTL) → empty dict.
        """
        cookies = self._django_session_cookies()
        if cookies and self._session_validation_fresh():
            return cookies

        if cookies:
            if self.validate_web_cookies(cookies):
                self._mark_session_validated()
                return cookies
            self.clear_web_cookies(reason='django_session_invalid')
            cookies = {}

        extra = self._extra()
        cached = extra.get('hs_web_cookies') or {}
        if isinstance(cached, dict) and cached:
            try:
                cached_at = float(extra.get('hs_web_cookies_at') or 0)
            except (TypeError, ValueError):
                cached_at = 0
            if cached_at and (time.time() - cached_at) < WEB_COOKIE_TTL_SECONDS:
                normalized = {str(k): str(v) for k, v in cached.items() if k and v}
                source = str(extra.get('hs_web_cookies_source') or 'tenant_cache')

                # Playwright-provisioned cookies: trust hubspotapi presence;
                # skip portal API probe (that endpoint needs OAuth, not session cookies).
                if source == 'playwright_provision':
                    if normalized.get('hubspotapi'):
                        self._mark_session_validated()
                        logger.info(
                            '[HubspotSession] playwright_provision cookies valid '
                            '(hubspotapi present, len=%d)',
                            len(normalized['hubspotapi']),
                        )
                        return normalized
                    # hubspotapi missing — re-provision needed
                    self.clear_web_cookies(reason='playwright_hubspotapi_missing')
                elif self.validate_web_cookies(normalized):
                    self.persist_web_cookies(normalized, source=source)
                    return normalized
                else:
                    self.clear_web_cookies(reason='tenant_cache_invalid')

        return {}

    @staticmethod
    def is_api_upstream_path(path: str) -> bool:
        low = (path or '').lower()
        return '/home/v2/api/' in low or '/firealarm/v4/alarm/' in low

    def cookies_for_upstream(self, *, client_path: str = '', method: str = 'GET') -> Dict[str, str]:
        """Odoo-style gate before forwarding cookies upstream."""
        path = (client_path or '').lower()
        if method.upper() == 'POST' and 'login' in path:
            return {}
        if self.is_api_upstream_path(path):
            return {}
        return self.ensure_web_cookies()
