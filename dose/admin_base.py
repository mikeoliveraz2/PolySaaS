"""
Base Admin class that ensures schema switching for tenant-specific models.
All tenant-specific ModelAdmin classes should inherit from this.
"""
from django.contrib import admin
from django.contrib.admin.models import DELETION, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import connection
import logging

logger = logging.getLogger(__name__)


def resolve_request_tenant(request):
    """
    Load Tenant from public without leaving search_path stuck on public.

    Do **not** use get_current_tenant() here for path switching — that helper
    restores the *previous* search_path after lookup, which often undoes a
    just-set tenant schema and leaves admin deletes on public (500).
    """
    from dose.models import Tenant

    slug = getattr(request, "current_tenant_slug", None)
    if not slug and hasattr(request, "session"):
        slug = request.session.get("tenant_slug") or request.session.get("tenant_id")

    with connection.cursor() as cur:
        cur.execute("SET search_path TO public;")

    tenant = None
    if slug:
        tenant = (
            Tenant.objects.filter(slug=slug, is_active=True).first()
            or Tenant.objects.filter(schema_name=slug, is_active=True).first()
            or Tenant.objects.filter(slug=slug).first()
            or Tenant.objects.filter(schema_name=slug).first()
        )
    if tenant is None:
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            try:
                from dose.models import UserProfile

                profile = (
                    UserProfile.objects.filter(user=user)
                    .select_related("tenant")
                    .first()
                )
                if profile and profile.tenant:
                    tenant = profile.tenant
            except Exception as exc:
                logger.warning("[TenantAwareModelAdmin] profile tenant lookup: %s", exc)
    return tenant


class TenantAwareModelAdmin(admin.ModelAdmin):
    """
    Base admin class that ensures queries use the correct tenant schema.
    Overrides get_queryset to ensure schema is set before querying.
    """

    def _set_tenant_search_path(self, request):
        """Point ORM at the request tenant schema (tenant data never in public)."""
        tenant = resolve_request_tenant(request)
        if tenant and getattr(tenant, "schema_name", None):
            connection.cursor().execute(
                f'SET search_path TO "{tenant.schema_name}", public;'
            )
            logger.info(
                "[TenantAwareModelAdmin] search_path=%s for %s",
                tenant.schema_name,
                self.model.__name__,
            )
            return tenant
        connection.cursor().execute("SET search_path TO public;")
        logger.warning(
            "[TenantAwareModelAdmin] search_path=public for %s (no tenant)",
            self.model.__name__,
        )
        return None

    def get_queryset(self, request):
        self._set_tenant_search_path(request)
        return super().get_queryset(request)

    def save_model(self, request, obj, form, change):
        import traceback

        self._set_tenant_search_path(request)
        try:
            super().save_model(request, obj, form, change)
        except Exception:
            logger.error(
                "[TenantAwareModelAdmin] save_model EXCEPTION for %s:\n%s",
                self.model.__name__,
                traceback.format_exc(),
            )
            raise

    def log_addition(self, request, obj, message):
        # Snapshot while on tenant path; write LogEntry on public only.
        self._set_tenant_search_path(request)

        def _write():
            connection.cursor().execute("SET search_path TO public;")
            return super(TenantAwareModelAdmin, self).log_addition(
                request, obj, message
            )

        try:
            return _write()
        finally:
            self._set_tenant_search_path(request)

    def log_change(self, request, obj, message):
        self._set_tenant_search_path(request)

        def _write():
            connection.cursor().execute("SET search_path TO public;")
            return super(TenantAwareModelAdmin, self).log_change(
                request, obj, message
            )

        try:
            return _write()
        finally:
            self._set_tenant_search_path(request)

    def log_deletion(self, request, obj, object_repr):
        object_id = obj.pk
        model = obj.__class__
        repr_text = (object_repr or str(obj))[:200]
        self._set_tenant_search_path(request)

        def _write():
            connection.cursor().execute("SET search_path TO public;")
            ct = ContentType.objects.get_for_model(model, for_concrete_model=False)
            return LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=ct.pk,
                object_id=object_id,
                object_repr=repr_text,
                action_flag=DELETION,
            )

        try:
            return _write()
        finally:
            self._set_tenant_search_path(request)

    def log_deletions(self, request, queryset):
        # Materialize on tenant schema — never re-query under public.
        self._set_tenant_search_path(request)
        items = [(obj.pk, str(obj)[:200]) for obj in queryset]
        model = queryset.model

        def _write():
            connection.cursor().execute("SET search_path TO public;")
            ct = ContentType.objects.get_for_model(model, for_concrete_model=False)
            return [
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ct.pk,
                    object_id=object_id,
                    object_repr=repr_text,
                    action_flag=DELETION,
                )
                for object_id, repr_text in items
            ]

        try:
            return _write()
        finally:
            self._set_tenant_search_path(request)

    def delete_model(self, request, obj):
        import traceback

        tenant = self._set_tenant_search_path(request)
        if tenant is None:
            raise PermissionDenied("No tenant schema — cannot delete tenant-owned row.")
        table = self.model._meta.db_table
        pk = obj.pk
        try:
            with connection.cursor() as cur:
                cur.execute(
                    f'DELETE FROM "{tenant.schema_name}"."{table}" WHERE id = %s',
                    [pk],
                )
            logger.info(
                "[TenantAwareModelAdmin] deleted %s id=%s schema=%s",
                self.model.__name__,
                pk,
                tenant.schema_name,
            )
        except Exception:
            logger.error(
                "[TenantAwareModelAdmin] delete_model failed %s id=%s:\n%s",
                self.model.__name__,
                pk,
                traceback.format_exc(),
            )
            raise

    def delete_queryset(self, request, queryset):
        import traceback

        tenant = self._set_tenant_search_path(request)
        if tenant is None:
            raise PermissionDenied("No tenant schema — cannot delete tenant-owned rows.")
        table = self.model._meta.db_table
        pks = list(queryset.values_list("pk", flat=True))
        if not pks:
            return
        try:
            placeholders = ", ".join(["%s"] * len(pks))
            with connection.cursor() as cur:
                cur.execute(
                    f'DELETE FROM "{tenant.schema_name}"."{table}" '
                    f"WHERE id IN ({placeholders})",
                    pks,
                )
            logger.info(
                "[TenantAwareModelAdmin] bulk deleted %s count=%s schema=%s",
                self.model.__name__,
                len(pks),
                tenant.schema_name,
            )
        except Exception:
            logger.error(
                "[TenantAwareModelAdmin] delete_queryset failed %s:\n%s",
                self.model.__name__,
                traceback.format_exc(),
            )
            raise
