"""
Update PassThroughEndpoints to use local URLs for demo/testing
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django_tenants.utils import schema_context
from dose.models import PassThroughEndpoint

def update_endpoints():
    with schema_context('public'):
    # Update or create osticket
    osticket = PassThroughEndpoint.objects.filter(menu_title__icontains='osticket').first()
    if osticket:
        osticket.endpoint_url = 'http://localhost:5000'
        osticket.save()
        print(f"Updated {osticket.menu_title} to {osticket.endpoint_url}")
    else:
        # Create osticket endpoint
        osticket = PassThroughEndpoint.objects.create(
            menu_title='OSTicket',
            endpoint_url='http://localhost:5000',
            trigger_path='dose/osticket/',
            is_enabled=True,
            show_in_menu=True,
            passthrough_type='scraper'
        )
        print(f"Created {osticket.menu_title} with {osticket.endpoint_url}")

    # Create or update Monitor Logger
    monitor = PassThroughEndpoint.objects.filter(menu_title__icontains='monitor').first()
    if monitor:
        monitor.endpoint_url = 'http://localhost:5000'
        monitor.save()
        print(f"Updated {monitor.menu_title} to {monitor.endpoint_url}")
    else:
        monitor = PassThroughEndpoint.objects.create(
            menu_title='Monitor Logger',
            endpoint_url='http://localhost:5000',
            trigger_path='dose/monitor/',
            is_enabled=True,
            show_in_menu=True,
            passthrough_type='scraper'
        )
        print(f"Created {monitor.menu_title} with {monitor.endpoint_url}")

    # Create or update PolySniffer
    polysniffer = PassThroughEndpoint.objects.filter(menu_title__icontains='polysniffer').first()
    if polysniffer:
        polysniffer.endpoint_url = 'http://localhost:5001'
        polysniffer.save()
        print(f"Updated {polysniffer.menu_title} to {polysniffer.endpoint_url}")
    else:
        polysniffer = PassThroughEndpoint.objects.create(
            menu_title='PolySniffer',
            endpoint_url='http://localhost:5001',
            trigger_path='dose/polysniffer/',
            is_enabled=True,
            show_in_menu=True,
            passthrough_type='html'
        )
        print(f"Created {polysniffer.menu_title} with {polysniffer.endpoint_url}")

if __name__ == '__main__':
    update_endpoints()