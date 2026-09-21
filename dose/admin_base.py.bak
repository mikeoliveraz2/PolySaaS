"""
Base Admin class that ensures schema switching for tenant-specific models.
All tenant-specific ModelAdmin classes should inherit from this.
"""
from django.contrib import admin
from django.contrib.admin.models import DELETION, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import connection
from dose.utils import get_current_tenant
import logging

logger = logging.getLogger(__name__)


class TenantAwareModelAdmin(admin.ModelAdmin):
    """
    Base admin class that ensures queries use the correct tenant schema.
    Overrides get_queryset to ensure schema is set before querying.
    """

    def _set_tenant_search_path(self, request):
        """Point ORM at the request tenant schema (tenant data never in public)."""
        tenant = get_current_tenant(request)
        if tenant and getattr(tenant, "schema_name", None):
            connection.cursor().execute(
                f'SET search_path TO "{tenant.schema_name}", public;'
            )
            logger.debug(
                "[TenantAwareModelAdmin] search_path=%s for %s",
                tenant.schema_name,
                self.model.__name__,
            )
            return tenant
        connection.cursor().execute("SET search_path TO public;")
        logger.debug(
            "[TenantAwareModelAdmin] search_path=public for %s (no tenant)",
            self.model.__name__,
        )
        return None

    def _with_public_search_path(self, request, fn):
        """
        Run ``fn`` with search_path=public (for LogEntry / ContentType), then
        restore the tenant schema. Never re-query tenant tables while public.
        """
        connection.cursor().execute("SET search_path TO public;")
        try:
            return fn()
        finally:
            self._set_tenant_search_path(request)

    def get_queryset(self, request):
        """Ensure schema is set before querying."""
        self._set_tenant_search_path(request)
        return super().get_queryset(request)

    def save_model(self, request, obj, form, change):
        """Ensure schema is set before saving. Tenant model row goes to tenant schema."""
        import traceback

        self._set_tenant_search_path(request)
        try:
            super().save_model(request, obj, form, change)
        except Exception:
            tb = traceback.format_exc()
            logger.error(
                "[TenantAwareModelAdmin] save_model EXCEPTION for %s:\n%s",
                self.model.__name__,
                tb,
            )
            raise

    # --- Django admin LogEntry writes (must use public) ---
    # Django calls log_deletion(s) *before* delete. Do NOT SET public and then
    # let Django re-evaluate a tenant queryset (webhook_mailbox missing → 500).
    # Materialize pk/repr first; write LogEntry only on public; restore tenant.

    def log_addition(self, request, obj, message):
        def _write():
            return super(TenantAwareModelAdmin, self).log_addition(
                request, obj, message
            )

        return self._with_public_search_path(request, _write)

    def log_change(self, request, obj, message):
        def _write():
            return super(TenantAwareModelAdmin, self).log_change(
                request, obj, message
            )

        return self._with_public_search_path(request, _write)

    def log_deletion(self, request, obj, object_repr):
        # Capture identifiers while still on tenant schema (caller path).
        object_id = obj.pk
        model = obj.__class__
        repr_text = (object_repr or str(obj))[:200]

        def _write():
            ct = ContentType.objects.get_for_model(model, for_concrete_model=False)
            return LogEntry.objects.log_action(
                user_id=request.user.pk,
                content_type_id=ct.pk,
                object_id=object_id,
                object_repr=repr_text,
                action_flag=DELETION,
            )

        return self._with_public_search_path(request, _write)

    def log_deletions(self, request, queryset):
        # Materialize on the *current* (tenant) path before touching public.
        self._set_tenant_search_path(request)
        items = [(obj.pk, str(obj)[:200]) for obj in queryset]
        model = queryset.model

        def _write():
            ct = ContentType.objects.get_for_model(model, for_concrete_model=False)
            entries = []
            for object_id, repr_text in items:
                entries.append(
                    LogEntry.objects.log_action(
                        user_id=request.user.pk,
                        content_type_id=ct.pk,
                        object_id=object_id,
                        object_repr=repr_text,
                        action_flag=DELETION,
                    )
                )
            return entries

        return self._with_public_search_path(request, _write)

    def delete_model(self, request, obj):
        """Delete tenant-owned row with explicit schema qualification."""
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
        """Bulk delete with schema-qualified SQL (no ORM re-query under public)."""
        import traceback

        tenant = self._set_tenant_search_path(request)
        if tenant is None:
            raise PermissionDenied("No tenant schema — cannot delete tenant-owned rows.")
        table = self.model._meta.db_table
        # Evaluate pks while on tenant path
        pks = list(queryset.values_list("pk", flat=True))
        if not pks:
            return
        try:
            with connection.cursor() as cur:
                placeholders = ", ".join(["%s"] * len(pks))
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
