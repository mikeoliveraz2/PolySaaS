# DO NOT MODIFY: Critical system file. Ask before making changes.
"""
App configuration for dose
"""
from django.apps import AppConfig


class DoseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dose'
    verbose_name = 'Dose Tenant Management'

    def ready(self):
        # CRITICAL: Import adapters FIRST to patch Site model for multi-tenant support
        # This must happen before django-allauth tries to query Site
        try:
            import dose.adapters  # noqa: F401 - This patches Site.objects.get/filter to use public schema
        except ImportError:
            pass  # adapters may not be available
        import dose.signals  # Import signals to connect them
        # Import polysniffer admin to register TrafficLog
        try:
            import dose.polysniffer.admin  # noqa: F401
        except ImportError:
            pass  # polysniffer may not be available


class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dose'

    def ready(self):
        import dose.signals  # Import signals to connect them
        # Import polysniffer admin to register TrafficLog
        try:
            import dose.polysniffer.admin  # noqa: F401
        except ImportError:
            pass  # polysniffer may not be available
