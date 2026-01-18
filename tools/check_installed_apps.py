"""Diagnostic: try importing each entry from INSTALLED_APPS and report errors.

Run with: python tools/check_installed_apps.py
It will load the DJANGO_SETTINGS_MODULE (defaults to mysite.settings) and
attempt to import each app entry, printing any exceptions and file origins.
"""
import importlib
import importlib.util
import os
import sys
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.environ.get('DJANGO_SETTINGS_MODULE', 'mysite.settings'))

def main():
    try:
        from django.conf import settings
    except Exception:
        # Try to import settings module directly
        try:
            settings_module = os.environ['DJANGO_SETTINGS_MODULE']
            settings = importlib.import_module(settings_module)
        except Exception:
            print('Failed to load Django settings:')
            traceback.print_exc()
            sys.exit(2)

    apps = getattr(settings, 'INSTALLED_APPS', None)
    if not apps:
        print('No INSTALLED_APPS found in settings; aborting.')
        sys.exit(1)

    print('Loaded settings from', os.environ.get('DJANGO_SETTINGS_MODULE'))
    for entry in apps:
        print('\n---')
        print('Entry:', entry)
        # If entry looks like a class path (app.apps.AppConfig), import module portion
        modname = entry
        if '.' in entry and entry.count('.') > 1 and entry.endswith('Config'):
            modname = '.'.join(entry.split('.')[:-1])

        try:
            spec = importlib.util.find_spec(modname)
            print('Spec:', spec)
            if spec is not None:
                origin = getattr(spec, 'origin', None)
                loader = getattr(spec, 'loader', None)
                print('Origin:', origin)
                print('Loader:', loader)
                # If origin is a file, try to read it to reproduce file read errors
                if origin and os.path.isfile(origin):
                    try:
                        with open(origin, 'rb') as f:
                            data = f.read(64)
                        print('Read OK (first 64 bytes):', data[:64])
                    except Exception as e:
                        print('Error reading origin file:')
                        traceback.print_exc()

            # Attempt to import the module
            imported = importlib.import_module(modname)
            print('Imported module:', modname, '->', imported)

        except Exception:
            print('Exception while importing', modname)
            traceback.print_exc()

if __name__ == '__main__':
    main()
