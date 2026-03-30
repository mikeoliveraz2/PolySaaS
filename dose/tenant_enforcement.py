from rest_framework import exceptions, permissions, viewsets

from dose.models import UserTenantMembership
from dose.utils import get_current_tenant

# Higher number = more privilege
ROLE_RANK = {
    UserTenantMembership.Role.VIEWER: 1,
    UserTenantMembership.Role.MEMBER: 2,
    UserTenantMembership.Role.ADMIN: 3,
    UserTenantMembership.Role.OWNER: 4,
}


def role_rank(role):
    if not role:
        return 0
    return ROLE_RANK.get(role, 0)


def role_at_least(role, minimum):
    """True if ``role`` is same or higher than ``minimum`` (both role string values)."""
    return role_rank(role) >= role_rank(minimum)


class TenantScopedViewSetMixin(viewsets.ModelViewSet):
    """
    Enforce tenant context, membership in user_tenant_memberships, and per-tenant role.
    """

    permission_classes = [permissions.IsAuthenticated]

    read_min_role = UserTenantMembership.Role.VIEWER
    write_min_role = UserTenantMembership.Role.MEMBER

    def _current_tenant(self):
        tenant = get_current_tenant(self.request)
        if not tenant:
            raise exceptions.PermissionDenied("No active tenant in request context.")
        return tenant

    def _active_membership(self, tenant):
        user = self.request.user
        if not user.is_authenticated:
            raise exceptions.NotAuthenticated()
        if user.is_superuser:
            return None
        try:
            return UserTenantMembership.objects.get(user=user, tenant=tenant)
        except UserTenantMembership.DoesNotExist:
            raise exceptions.PermissionDenied(
                "No membership for this user in the active tenant."
            )

    def _min_role_for_action(self):
        if self.action in ("list", "retrieve", "metadata"):
            return self.read_min_role
        return self.write_min_role

    def _require_role_for_action(self, membership):
        if self.request.user.is_superuser:
            return
        if membership is None:
            raise exceptions.PermissionDenied(
                "No membership for this user in the active tenant."
            )
        need = self._min_role_for_action()
        role = membership.role
        if not role_at_least(role, need):
            raise exceptions.PermissionDenied(
                f"This action requires role {need} or higher in the current tenant."
            )

    def get_queryset(self):
        base_qs = super().get_queryset()
        tenant = self._current_tenant()
        membership = self._active_membership(tenant)
        self._require_role_for_action(membership)

        model_fields = {f.name for f in base_qs.model._meta.get_fields()}
        if "tenant" in model_fields:
            return base_qs.filter(tenant=tenant)
        return base_qs

    def perform_create(self, serializer):
        tenant = self._current_tenant()
        membership = self._active_membership(tenant)
        self._require_role_for_action(membership)
        model_fields = {f.name for f in serializer.Meta.model._meta.get_fields()}
        if "tenant" in model_fields:
            serializer.save(tenant=tenant)
        else:
            serializer.save()

    def perform_update(self, serializer):
        tenant = self._current_tenant()
        membership = self._active_membership(tenant)
        self._require_role_for_action(membership)
        instance = self.get_object()
        if hasattr(instance, "tenant") and instance.tenant_id != tenant.id:
            raise exceptions.PermissionDenied("Cross-tenant write denied.")
        serializer.save()

    def perform_destroy(self, instance):
        tenant = self._current_tenant()
        membership = self._active_membership(tenant)
        self._require_role_for_action(membership)
        if hasattr(instance, "tenant") and instance.tenant_id != tenant.id:
            raise exceptions.PermissionDenied("Cross-tenant delete denied.")
        instance.delete()
