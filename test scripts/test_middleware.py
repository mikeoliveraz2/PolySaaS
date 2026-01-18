import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from dose.middleware.jazzmin_tenant_theme import JazzminTenantThemeMiddleware

# Create a mock request
factory = RequestFactory()
request = factory.get('/admin/')
request.user = User.objects.filter(is_superuser=True).first()
if not request.user:
    print('No superuser found')
    exit()

request.session = {}

# Create middleware instance
middleware = JazzminTenantThemeMiddleware(lambda req: None)

# Process the request
middleware.process_request(request)

print('Middleware processed successfully')
if hasattr(request, 'jazzmin_settings'):
    topmenu_links = request.jazzmin_settings.get('topmenu_links', [])
    print(f'Total top menu links: {len(topmenu_links)}')

    osticket_links = [link for link in topmenu_links if 'osticket' in link.get('url', '').lower() or 'osticket' in link.get('name', '').lower()]
    print(f'OSTicket links found: {len(osticket_links)}')

    for link in osticket_links:
        print(f'  - Name: {link.get("name")}')
        print(f'    URL: {link.get("url")}')
        print(f'    Icon: {link.get("icon", "None")}')
        print(f'    Permissions: {link.get("permissions", [])}')
else:
    print('No jazzmin_settings found')