"""
Base Admin class that ensures schema switching for tenant-specific models.
All tenant-specific ModelAdmin classes should inherit from this.
"""
from django.contrib import admin
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

    # --- Django admin infrastructure log writes ---
    # django_admin_log has a FK → auth_user. Authentication uses public.auth_user,
    # so admin log writes MUST target public.django_admin_log.
    #
    # CRITICAL: Django calls log_deletion(s) *before* delete_model/delete_queryset.
    # SET LOCAL public for the log must not leave search_path on public for the
    # subsequent tenant-table DELETE (e.g. webhook_mailbox → 500).

    def log_addition(self, request, obj, message):
        with connection.cursor() as cur:
            cur.execute("SET LOCAL search_path TO public;")
        try:
            return super().log_addition(request, obj, message)
        finally:
            self._set_tenant_search_path(request)

    def log_change(self, request, obj, message):
        with connection.cursor() as cur:
            cur.execute("SET LOCAL search_path TO public;")
        try:
            return super().log_change(request, obj, message)
        finally:
            self._set_tenant_search_path(request)

    def log_deletion(self, request, obj, object_repr):
        with connection.cursor() as cur:
            cur.execute("SET LOCAL search_path TO public;")
        try:
            return super().log_deletion(request, obj, object_repr)
        finally:
            self._set_tenant_search_path(request)

    def log_deletions(self, request, queryset):
        with connection.cursor() as cur:
            cur.execute("SET LOCAL search_path TO public;")
        try:
            return super().log_deletions(request, queryset)
        finally:
            self._set_tenant_search_path(request)

    def delete_model(self, request, obj):
        """Ensure schema is set before deleting tenant-owned rows."""
        self._set_tenant_search_path(request)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """Bulk admin delete — same schema restore as delete_model."""
        self._set_tenant_search_path(request)
        super().delete_queryset(request, queryset)
