# Tenant context: resolves active tenant + role, syncs session, then SessionTenantMiddleware can set search_path.
# Must run after AuthenticationMiddleware and before SessionTenantMiddleware.

import logging

from django.db import connection
from django.utils.deprecation import MiddlewareMixin

from dose.models import Tenant, UserTenantMembership
from dose.tenant_jwt import decode_tenant_claims_from_bearer
from dose.tenant_session import apply_tenant_to_session

logger = logging.getLogger(__name__)


def _tenant_from_public_slug(tenant_slug):
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL search_path TO public;")
    return Tenant.objects.filter(slug=tenant_slug, is_active=True).first()


class TenantContextMiddleware(MiddlewareMixin):
    """
    Resolve ``request.current_tenant_id`` and ``request.current_tenant_role``,
    optionally align session tenant (so SessionTenantMiddleware sets the right schema).

    Priority for tenant: ``X-Tenant-Slug`` > HS256 Bearer ``tenant_slug`` claim > session.
    """

    def process_request(self, request):
        request.current_tenant_id = None
        request.current_tenant_role = None
        request.current_tenant_slug = None

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None

        tenant_slug = None
        jwt_role = None

        header_tenant_slug = request.META.get("HTTP_X_TENANT_SLUG")
        if header_tenant_slug is not None and str(header_tenant_slug).strip():
            tenant_slug = str(header_tenant_slug).strip()

        auth = request.META.get("HTTP_AUTHORIZATION", "")
        claims = decode_tenant_claims_from_bearer(auth)
        if claims:
            if tenant_slug is None:
                tenant_slug = claims.get("tenant_slug")
            jwt_role = claims.get("tenant_role")

        if tenant_slug is None:
            tenant_slug = request.session.get("tenant_slug")
        if tenant_slug is None:
            tid = request.session.get("tenant_id")
            if tid is not None and str(tid).strip():
                tenant_slug = str(tid).strip()
                request.session["tenant_slug"] = tenant_slug
                request.session.pop("tenant_id", None)
                request.session.save()

        if tenant_slug is None:
            return None

        if getattr(user, "is_superuser", False):
            request.current_tenant_id = tenant_slug
            request.current_tenant_slug = tenant_slug
            m = UserTenantMembership.objects.filter(
                user_id=user.id, tenant__slug=tenant_slug
            ).first()
            request.current_tenant_role = m.role if m else "owner"
            tenant = _tenant_from_public_slug(tenant_slug)
            if tenant and (
                request.session.get("tenant_slug") != tenant_slug
                or (m and request.session.get("tenant_role") != m.role)
            ):
                apply_tenant_to_session(request, tenant, m)
            return None

        try:
            m = UserTenantMembership.objects.get(user_id=user.id, tenant__slug=tenant_slug)
        except UserTenantMembership.DoesNotExist:
            logger.warning(
                "TenantContextMiddleware: no membership user=%s tenant_slug=%s — clearing session tenant",
                user.pk,
                tenant_slug,
            )
            for k in (
                "tenant_name",
                "tenant_slug",
                "tenant_description",
                "tenant_logo_url",
                "tenant_role",
            ):
                request.session.pop(k, None)
            request.session.save()
            return None

        request.current_tenant_id = tenant_slug
        request.current_tenant_slug = tenant_slug
        request.current_tenant_role = m.role
        if jwt_role and jwt_role == m.role:
            request.current_tenant_role = jwt_role

        tenant = _tenant_from_public_slug(tenant_slug)
        if tenant and (
            request.session.get("tenant_slug") != tenant_slug
            or request.session.get("tenant_role") != m.role
        ):
            apply_tenant_to_session(request, tenant, m)

        return None
