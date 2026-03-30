# Tenant context: resolves active tenant + role, syncs session, then SessionTenantMiddleware can set search_path.
# Must run after AuthenticationMiddleware and before SessionTenantMiddleware.

import logging

from django.db import connection
from django.utils.deprecation import MiddlewareMixin

from dose.models import Tenant, UserTenantMembership
from dose.tenant_jwt import decode_tenant_claims_from_bearer
from dose.tenant_session import apply_tenant_to_session

logger = logging.getLogger(__name__)


def _tenant_from_public_pk(tenant_id):
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL search_path TO public;")
    return Tenant.objects.filter(pk=tenant_id, is_active=True).first()


class TenantContextMiddleware(MiddlewareMixin):
    """
    Resolve ``request.current_tenant_id`` and ``request.current_tenant_role``,
    optionally align session tenant (so SessionTenantMiddleware sets the right schema).

    Priority for tenant id: ``X-Tenant-Id`` > HS256 Bearer ``tenant_id`` claim > session.
    """

    def process_request(self, request):
        request.current_tenant_id = None
        request.current_tenant_role = None

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None

        tenant_id = None
        jwt_role = None

        header_tid = request.META.get("HTTP_X_TENANT_ID")
        if header_tid is not None and str(header_tid).strip().isdigit():
            tenant_id = int(header_tid)

        auth = request.META.get("HTTP_AUTHORIZATION", "")
        claims = decode_tenant_claims_from_bearer(auth)
        if claims:
            if tenant_id is None:
                tenant_id = claims["tenant_id"]
            jwt_role = claims.get("tenant_role")

        if tenant_id is None:
            tid = request.session.get("tenant_id")
            if tid is not None:
                try:
                    tenant_id = int(tid)
                except (TypeError, ValueError):
                    tenant_id = None

        if tenant_id is None:
            return None

        if getattr(user, "is_superuser", False):
            request.current_tenant_id = tenant_id
            m = UserTenantMembership.objects.filter(
                user_id=user.id, tenant_id=tenant_id
            ).first()
            request.current_tenant_role = m.role if m else "owner"
            tenant = _tenant_from_public_pk(tenant_id)
            if tenant and (
                request.session.get("tenant_id") != tenant_id
                or (m and request.session.get("tenant_role") != m.role)
            ):
                apply_tenant_to_session(request, tenant, m)
            return None

        try:
            m = UserTenantMembership.objects.get(user_id=user.id, tenant_id=tenant_id)
        except UserTenantMembership.DoesNotExist:
            logger.warning(
                "TenantContextMiddleware: no membership user=%s tenant_id=%s — clearing session tenant",
                user.pk,
                tenant_id,
            )
            for k in (
                "tenant_id",
                "tenant_name",
                "tenant_slug",
                "tenant_description",
                "tenant_logo_url",
                "tenant_role",
            ):
                request.session.pop(k, None)
            request.session.save()
            return None

        request.current_tenant_id = tenant_id
        request.current_tenant_role = m.role
        if jwt_role and jwt_role == m.role:
            request.current_tenant_role = jwt_role

        tenant = _tenant_from_public_pk(tenant_id)
        if tenant and (
            request.session.get("tenant_id") != tenant_id
            or request.session.get("tenant_role") != m.role
        ):
            apply_tenant_to_session(request, tenant, m)

        return None
