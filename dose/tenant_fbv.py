"""
Shared checks for function-based views: tenant + UserTenantMembership + role.

Never use UserProfile for access control; use membership only.
"""

from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse

from dose.models import UserTenantMembership
from dose.tenant_enforcement import role_at_least
from dose.utils import get_current_tenant


def _strict_enforcement():
    return getattr(settings, "STRICT_TENANT_ENFORCEMENT", False)


def _deny(msg, *, json_errors, status=403):
    if json_errors:
        return JsonResponse({"success": False, "error": msg}, status=status)
    return HttpResponseForbidden(msg)


def require_tenant_membership_for_fbv(
    request,
    min_role=None,
    *,
    json_errors=True,
):
    """
    Validate active tenant and membership (and optional minimum role).

    Returns ``(tenant, membership, None)`` on success. ``membership`` is ``None``
    when the user is a superuser and strict enforcement is off.

    On failure returns ``(None, None, response)``.
    """
    tenant = get_current_tenant(request)
    if not tenant:
        return None, None, _deny("No active tenant", json_errors=json_errors, status=400)

    if not request.user.is_authenticated:
        return None, None, _deny(
            "Authentication required", json_errors=json_errors, status=401
        )

    if request.user.is_superuser and not _strict_enforcement():
        return tenant, None, None

    try:
        m = UserTenantMembership.objects.get(user=request.user, tenant=tenant)
    except UserTenantMembership.DoesNotExist:
        return None, None, _deny("No membership in this tenant", json_errors=json_errors)

    if min_role is not None and not role_at_least(m.role, min_role):
        return None, None, _deny("Insufficient role for this action", json_errors=json_errors)

    return tenant, m, None


def user_can_manage_tenant_settings(request, tenant):
    """Whether the user may change tenant name/settings (admin+ or privileged superuser)."""
    if not request.user.is_authenticated:
        return False
    if request.user.is_superuser and not _strict_enforcement():
        return True
    try:
        m = UserTenantMembership.objects.get(user=request.user, tenant=tenant)
    except UserTenantMembership.DoesNotExist:
        return False
    return role_at_least(m.role, UserTenantMembership.Role.ADMIN)
