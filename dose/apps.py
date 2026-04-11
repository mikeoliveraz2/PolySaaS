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
        # CRITICAL: Patch Site model FIRST for multi-tenant support.
        # _patch_site_model() is called here (inside ready()) rather than at
        # module import time so that no database operations occur during worker
        # startup before the database connection is available.
        try:
            from dose.adapters import _patch_site_model
            _patch_site_model()
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
