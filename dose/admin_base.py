"""
Base Admin class that ensures schema switching for tenant-specific models.
All tenant-specific ModelAdmin classes should inherit from this.
"""
from django.contrib import admin
from django.db import connection
from dose.utils import get_current_tenant
import logging

class TenantAwareModelAdmin(admin.ModelAdmin):
    """
    Base admin class that ensures queries use the correct tenant schema.
    Overrides get_queryset to ensure schema is set before querying.
    """

    def get_queryset(self, request):
        """Ensure schema is set before querying."""
        # Get current tenant and set schema
        tenant = get_current_tenant(request)
        logger = logging.getLogger(__name__)
        if tenant and tenant.schema_name:
            # Set search_path directly on the connection (not in cursor context)
            # This ensures it persists for Django ORM operations
            connection.cursor().execute(f'SET search_path TO "{tenant.schema_name}",public;')
            logger.debug(f"[TenantAwareModelAdmin] Set search_path to {tenant.schema_name} for {self.model.__name__} queryset")
        else:
            connection.cursor().execute("SET search_path TO public;")
            logger.debug(f"[TenantAwareModelAdmin] Set search_path to public for {self.model.__name__} queryset (no tenant)")

        # Now get the queryset - it will use the correct schema
        queryset = super().get_queryset(request)
        return queryset

    def save_model(self, request, obj, form, change):
        """Ensure schema is set before saving. Tenant model row goes to tenant schema."""
        import traceback
        import logging
        tenant = get_current_tenant(request)
        if tenant and tenant.schema_name:
            connection.cursor().execute(f'SET search_path TO "{tenant.schema_name}",public;')
            logger = logging.getLogger(__name__)
            logger.debug(f"[TenantAwareModelAdmin] Set search_path to {tenant.schema_name} for {self.model.__name__} save")
        else:
            connection.cursor().execute("SET search_path TO public;")
            logger = logging.getLogger(__name__)
            logger.debug(f"[TenantAwareModelAdmin] Set search_path to public for {self.model.__name__} save (no tenant)")

        try:
            super().save_model(request, obj, form, change)
        except Exception as exc:
            tb = traceback.format_exc()
            logging.getLogger(__name__).error(
                "[TenantAwareModelAdmin] save_model EXCEPTION for %s:\n%s",
                self.model.__name__,
                tb,
            )
            raise  # re-raise so subclass save_model can catch and display it

    # --- Django admin infrastructure log writes ---
    # django_admin_log has a FK → auth_user. Authentication uses public.auth_user,
    # so admin log writes MUST target public.django_admin_log.
    # These overrides use SET LOCAL so the tenant search_path is unaffected outside
    # the savepoint — tenant data stays in the tenant schema.

    def log_addition(self, request, obj, message):
        with connection.cursor() as cur:
            cur.execute("SET LOCAL search_path TO public;")
        super().log_addition(request, obj, message)

    def log_change(self, request, obj, message):
        with connection.cursor() as cur:
            cur.execute("SET LOCAL search_path TO public;")
        super().log_change(request, obj, message)

    def log_deletion(self, request, obj, object_repr):
        with connection.cursor() as cur:
            cur.execute("SET LOCAL search_path TO public;")
        super().log_deletion(request, obj, object_repr)

    def delete_model(self, request, obj):
        """Ensure schema is set before deleting."""
        tenant = get_current_tenant(request)
        logger = logging.getLogger(__name__)
        if tenant and tenant.schema_name:
            # Set search_path directly on the connection (not in cursor context)
            connection.cursor().execute(f'SET search_path TO "{tenant.schema_name}",public;')
            logger.debug(f"[TenantAwareModelAdmin] Set search_path to {tenant.schema_name} for {self.model.__name__} delete")
        else:
            connection.cursor().execute("SET search_path TO public;")
            logger.debug(f"[TenantAwareModelAdmin] Set search_path to public for {self.model.__name__} delete (no tenant)")

        super().delete_model(request, obj)

