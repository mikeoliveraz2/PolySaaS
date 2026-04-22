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
        import sys
        print("[Django] DoseConfig.ready() starting", flush=True, file=sys.stderr)
        try:
            print("[Django] Importing dose.adapters", flush=True, file=sys.stderr)
            import dose.adapters  # noqa: F401 - This patches Site.objects.get/filter to use public schema
            print("[Django] dose.adapters imported", flush=True, file=sys.stderr)
        except ImportError as e:
            print(f"[Django] Failed to import dose.adapters: {e}", flush=True, file=sys.stderr)
            pass  # adapters may not be available
        print("[Django] Importing dose.signals", flush=True, file=sys.stderr)
        import dose.signals  # Import signals to connect them
        print("[Django] dose.signals imported", flush=True, file=sys.stderr)
        # Import polysniffer admin to register TrafficLog
        try:
            print("[Django] Importing dose.polysniffer.admin", flush=True, file=sys.stderr)
            import dose.polysniffer.admin  # noqa: F401
            print("[Django] dose.polysniffer.admin imported", flush=True, file=sys.stderr)
        except ImportError as e:
            print(f"[Django] Failed to import dose.polysniffer.admin: {e}", flush=True, file=sys.stderr)
            pass  # polysniffer may not be available

        # Startup registry diagnostic — visible in Render boot logs.
        # Compare registry_len here vs admin_index_diag log on /admin/ hit to detect
        # whether models are registered but hidden (Jazzmin/permissions) or never registered.
        try:
            from django.contrib import admin as _admin_site
            _reg_len = len(getattr(_admin_site.site, "_registry", {}) or {})
            print(
                f"[admin_registry_diag] ready() registry_len={_reg_len}",
                flush=True,
                file=sys.stderr,
            )
        except Exception as _e:
            print(f"[admin_registry_diag] could not read registry: {_e}", flush=True, file=sys.stderr)

        print("[Django] DoseConfig.ready() completed", flush=True, file=sys.stderr)


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
