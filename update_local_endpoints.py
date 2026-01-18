"""
Update all 5 passthrough endpoints in olient schema to point to local Traefik URLs
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from dose.models import PassThroughEndpoint
from django.db import connection

# Local Traefik endpoints
endpoints_config = [
    {
        'trigger_path': 'osticket',
        'endpoint_url': 'https://osticket.polysaas.online',
        'menu_title': 'OsTicket',
        'provider': 'Custom'
    },
    {
        'trigger_path': 'nextcloud',
        'endpoint_url': 'https://nextcloud.polysaas.online',
        'menu_title': 'Nextcloud',
        'provider': 'Custom'
    },
    {
        'trigger_path': 'odoo',
        'endpoint_url': 'https://odoo.polysaas.online',
        'menu_title': 'Odoo',
        'provider': 'Custom'
    },
    {
        'trigger_path': 'suitecrm',
        'endpoint_url': 'https://suitecrm.polysaas.online',
        'menu_title': 'SuiteCRM',
        'provider': 'Custom'
    },
    {
        'trigger_path': 'dolibarr',
        'endpoint_url': 'https://dolibarr.polysaas.online',
        'menu_title': 'Dolibarr',
        'provider': 'Custom'
    }
]

# Switch to olient schema
connection.set_schema('olient')

print("Updating endpoints in olient schema...")

for config in endpoints_config:
    endpoint, created = PassThroughEndpoint.objects.update_or_create(
        trigger_path=config['trigger_path'],
        defaults={
            'endpoint_url': config['endpoint_url'],
            'menu_title': config['menu_title'],
            'provider': config['provider'],
            'is_enabled': True,
            'show_in_menu': True
        }
    )

    action = "Created" if created else "Updated"
    print(f"  {action}: {endpoint.menu_title} ({endpoint.trigger_path}) -> {endpoint.endpoint_url}")

print(f"\nTotal endpoints in olient schema: {PassThroughEndpoint.objects.count()}")
print("\nAll endpoints:")
for ep in PassThroughEndpoint.objects.all().order_by('menu_title'):
    status = "✓ Enabled" if ep.is_enabled else "✗ Disabled"
    print(f"  {status} - {ep.menu_title}: {ep.trigger_path} -> {ep.endpoint_url}")
