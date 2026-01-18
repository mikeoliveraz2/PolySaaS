import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# Import dose.urls BEFORE django.setup()
print("[TEST] Importing dose.urls BEFORE django.setup()...")
try:
    import dose.urls as urls_module
    print(f"[TEST] Imported from: {urls_module.__file__}")
    print(f"[TEST] Total patterns: {len(urls_module.urlpatterns)}")
except Exception as e:
    print(f"[TEST] Import failed: {e}")
    import traceback
    traceback.print_exc()

# Check if file was created
if os.path.exists('DOSE_URLS_LOADED.txt'):
    with open('DOSE_URLS_LOADED.txt') as f:
        print(f"[TEST] SUCCESS! File contains: {f.read().strip()}")
else:
    print("[TEST] FAILURE! File was not created - module code did NOT execute!")
