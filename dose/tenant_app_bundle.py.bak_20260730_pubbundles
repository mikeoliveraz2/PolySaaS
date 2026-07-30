"""
Req 6: per-tenant application bundle — TenantApp must exist and be active.

Use ``TenantApp.public_bundles`` (public schema) for lookups so tenant
search_path does not hide bundle rows.
"""

from rest_framework.permissions import BasePermission

from dose.models import TenantApp
from dose.utils import get_current_tenant


def tenant_has_active_bundle(tenant, app_name: str) -> bool:
    """True if ``app_name`` is in this tenant's bundle with status *active*."""
    if not tenant or not app_name:
        return False
    return TenantApp.public_bundles.filter(
        tenant_id=tenant.id,
        app_name=app_name,
        status="active",
    ).exists()


class TenantAppBundlePermission(BasePermission):
    """
    DRF permission: set ``required_tenant_app`` on the view (e.g. ``'mattermost'``).
    Denies if the app is not in the tenant's bundle with status *active*.
    If ``required_tenant_app`` is unset, allows (no bundle check).
    """

    message = "This application is not enabled for your current tenant."

    def has_permission(self, request, view):
        app_name = getattr(view, "required_tenant_app", None)
        if not app_name:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        tenant = get_current_tenant(request)
        if not tenant:
            return False
        return tenant_has_active_bundle(tenant, app_name)


class TenantAppBundledViewSetMixin:
    """
    Combine with a DRF viewset (after ``TenantScopedViewSetMixin`` or any
    viewset that defines ``get_permissions``). Set ``required_tenant_app`` to a
    :class:`dose.models.TenantApp` ``app_name`` value (e.g. ``'mattermost'``).

    Appends :class:`TenantAppBundlePermission` only when ``required_tenant_app`` is set.
    """

    def get_permissions(self):
        perms = super().get_permissions()
        if getattr(self, "required_tenant_app", None):
            perms.append(TenantAppBundlePermission())
        return perms
