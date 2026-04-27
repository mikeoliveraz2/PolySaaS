"""
Passthrough authentication middleware (POL-2 / R-2).

Injects user identity headers into passthrough requests so downstream
bundled apps can auto-login without a second authentication step.

Two modes (configured via settings.PASSTHROUGH_AUTH_MODE):
  - 'header' : Simple HTTP headers (REMOTE_USER, X-User-Email, etc.)
  - 'jwt'    : Signed JWT in Authorization: Bearer header

Runs BEFORE ExternalPassthroughMiddleware so forwarded requests carry
the auth payload. The existing forwarding.py already copies HTTP_*
headers from request.META into outgoing requests (line 61).

Credit: Architecture by Shela, implementation by Desktop-CC.
"""
import time
import logging

import jwt  # PyJWT (already in requirements)
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


def _get_tenant_info(user):
    """Safely extract tenant info from user's profile."""
    try:
        profile = getattr(user, 'userprofile', None)
        if profile and profile.tenant:
            return {
                'tenant_name': profile.tenant.name,
                'tenant_slug': profile.tenant.slug,
            }
    except Exception:
        pass
    return {}


class PassthroughAuthMiddleware(MiddlewareMixin):
    """
    Injects authentication into passthrough requests.

    Mode is determined by settings.PASSTHROUGH_AUTH_MODE ('header' or 'jwt').
    Only fires for authenticated users on passthrough routes (/pt/).
    """

    # Paths that trigger header injection
    PASSTHROUGH_PREFIXES = ('/pt/',)

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        if not any(request.path.startswith(p) for p in self.PASSTHROUGH_PREFIXES):
            return None

        mode = getattr(settings, 'PASSTHROUGH_AUTH_MODE', 'header')

        if mode == 'jwt':
            self._inject_jwt(request)
        else:
            self._inject_headers(request)

        self._inject_app_token(request)

        return None

    def _inject_headers(self, request):
        """Simple header injection — fastest to get working."""
        user = request.user
        headers = {
            'X-User-ID': str(user.id),
            'X-User-Email': user.email,
            'X-User-Name': user.get_full_name() or user.username,
            'X-User-Is-Staff': 'true' if user.is_staff else 'false',
            'REMOTE_USER': user.email,
        }

        tenant_info = _get_tenant_info(user)
        if tenant_info:
            headers['X-Tenant-Name'] = tenant_info['tenant_name']
            headers['X-Tenant-Slug'] = tenant_info['tenant_slug']

        for key, value in headers.items():
            meta_key = f'HTTP_{key.upper().replace("-", "_")}'
            request.META[meta_key] = value

        logger.debug("Injected auth headers for %s -> %s", user.email, request.path)

    def _inject_jwt(self, request):
        """Signed JWT in Authorization: Bearer — verifiable by downstream apps."""
        user = request.user

        payload = {
            'sub': str(user.id),
            'email': user.email,
            'name': user.get_full_name() or user.username,
            'is_staff': user.is_staff,
            'iat': int(time.time()),
            'exp': int(time.time()) + getattr(settings, 'PASSTHROUGH_JWT_EXPIRY', 300),
            'iss': 'polysaas',
        }

        tenant_info = _get_tenant_info(user)
        payload.update(tenant_info)

        # Use RSA key from OIDC config if available (RS256), else fall back to HS256
        oidc_key = getattr(settings, 'OAUTH2_PROVIDER', {}).get('OIDC_RSA_PRIVATE_KEY', '')
        if oidc_key:
            token = jwt.encode(payload, oidc_key, algorithm='RS256')
        else:
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'

        logger.debug("Injected JWT for %s -> %s", user.email, request.path)

    # ------------------------------------------------------------------
    # App-specific token injection
    # ------------------------------------------------------------------

    _TOKEN_KEYS = {
        'mattermost': 'mm_token',
    }

    def _inject_app_token(self, request):
        """
        Look up the app trigger from the path, find the TenantApp,
        and inject the app-specific auth token if one is stored.
        """
        parts = request.path.strip('/').split('/')
        if len(parts) < 3 or parts[0] != 'pt':
            return

        trigger = parts[2].lower()
        token_key = self._TOKEN_KEYS.get(trigger)
        if not token_key:
            return

        try:
            from dose.models import TenantApp
            from dose.utils import get_current_tenant

            tenant = get_current_tenant(request)
            if not tenant:
                return

            ta = TenantApp.objects.filter(
                tenant=tenant, app_name=trigger, status='active',
            ).first()
            if not ta or not ta.extra_config:
                return

            app_token = ta.extra_config.get(token_key)
            if app_token:
                request.META['HTTP_AUTHORIZATION'] = f'Bearer {app_token}'
                logger.debug(
                    "Injected %s app token for %s -> %s",
                    trigger, request.user.email, request.path,
                )
        except Exception as exc:
            logger.warning("App token injection failed for %s: %s", trigger, exc)
