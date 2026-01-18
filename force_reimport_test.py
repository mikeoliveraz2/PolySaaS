import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

# Delete dose.urls from cache if it exists
if 'dose.urls' in sys.modules:
    del sys.modules['dose.urls']
    print("Deleted dose.urls from sys.modules cache")

# Force reimport
import dose.urls
print(f"Reimported dose.urls from: {dose.urls.__file__}")
print(f"Total patterns: {len(dose.urls.urlpatterns)}")

# Check if file was created
if os.path.exists('DOSE_URLS_LOADED.txt'):
    with open('DOSE_URLS_LOADED.txt') as f:
        print(f"SUCCESS! File contains: {f.read().strip()}")
else:
    print("FAILURE! File was not created - module code did NOT execute!")
