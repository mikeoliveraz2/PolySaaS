"""Seed HubSpot portlet definitions and optional orchestration Instructions."""
from django.core.management.base import BaseCommand
from django.db import connection

from dose.models import Instruction, Tenant
from dose.views.hubspot_context import DEFAULT_PORTLETS, _seed_portlet_definitions


class Command(BaseCommand):
    help = 'Seed HubSpot portlet definitions and optional list Instructions for a tenant schema.'

    def add_arguments(self, parser):
        parser.add_argument('tenant_slug', nargs='?', default='olient')
        parser.add_argument('--instructions', action='store_true', help='Create hubspot:* list Instructions')

    def handle(self, *args, **options):
        slug = options['tenant_slug']
        tenant = Tenant.objects.filter(slug=slug).first()
        if not tenant:
            self.stderr.write(f'Tenant not found: {slug}')
            return

        _seed_portlet_definitions(tenant)
        self.stdout.write(self.style.SUCCESS(f'Seeded HubSpot portlets for {slug}'))

        if not options['instructions']:
            return

        with connection.cursor() as cur:
            cur.execute(f'SET search_path TO "{tenant.schema_name}", public')

        for pslug, title, script, _icon, _order in DEFAULT_PORTLETS:
            path = f'/dose/api/hubspot/portlets/{pslug}/'
            Instruction.objects.update_or_create(
                tenant=tenant,
                requestpath=path,
                direction='REQ',
                requestmethod='GET',
                defaults={
                    'match_type': 'path',
                    'executescript': script,
                    'eventKey': f'hubspot:{pslug}:list',
                    'description': f'HubSpot {title} portlet list',
                    'save_callbackdata': False,
                },
            )
        self.stdout.write(self.style.SUCCESS(f'Seeded HubSpot Instructions for {slug}'))
