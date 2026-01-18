#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # CRITICAL: Auto-migrate ALL schemas in multi-tenant system
    # When 'migrate' is called, redirect to migrate_all_schemas command
    if 'migrate' in sys.argv and 'migrate_all_schemas' not in sys.argv:
        print("\n" + "="*80)
        print("[*] Multi-Tenant Migration Redirect")
        print("    Using migrate_all_schemas to handle all tenant schemas...")
        print("="*80 + "\n")

        # Replace 'migrate' with 'migrate_all_schemas' in argv and re-execute
        sys.argv[sys.argv.index('migrate')] = 'migrate_all_schemas'
        execute_from_command_line(sys.argv)
        sys.exit(0)  # Exit after redirecting to migrate_all_schemas

    execute_from_command_line(sys.argv)
