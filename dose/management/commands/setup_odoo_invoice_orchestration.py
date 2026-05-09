"""
Management command: setup_odoo_invoice_orchestration

Creates the two Instructions needed for the demo orchestration flow:

  1. DETECTOR — matches Odoo invoice create POST in the passthrough:
       requestpath: /web/dataset/call_kw/account.move/create
       executescript: EndpointDataExtractorService
       → publishes message to local MQ (or in-process) on topic polysaas.odoo.invoice.created

  2. CONSUMER — matches the MQ routing path:
       requestpath: /mq/polysaas.odoo.invoice
       executescript: OdooInvoiceNotifierService
       → posts Mattermost notification

Usage:
    python manage.py setup_odoo_invoice_orchestration --tenant polysaas
    python manage.py setup_odoo_invoice_orchestration --tenant polysaas --dry-run
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = 'Wire Odoo invoice → Mattermost notification orchestration'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', default='polysaas', help='Tenant slug')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be created, no writes')

    def handle(self, *args, **options):
        tenant_slug = options['tenant']
        dry_run = options['dry_run']

        from dose.models import Tenant
        try:
            tenant = Tenant.objects.get(slug=tenant_slug)
        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant "{tenant_slug}" not found')

        schema = tenant.slug
        with connection.cursor() as cur:
            cur.execute(f'SET search_path TO "{schema}", public;')

        self.stdout.write(f'Tenant: {tenant.name} (schema={schema})')

        from dose.models import Instruction

        INSTRUCTIONS = [
            {
                'label': 'DETECTOR — Odoo invoice create passthrough hook',
                'requestpath': '/web/dataset/call_kw/account.move/create',
                'requestmethod': 'POST',
                'direction': 'REQ',
                'eventKey': 'polysaas.odoo.invoice.created',
                'executescript': 'EndpointDataExtractorService',
                'description': 'Detect Odoo invoice create via passthrough → extract & publish to MQ',
                'save_callbackdata': True,
            },
            {
                'label': 'CONSUMER — Post Odoo invoice notification to Mattermost',
                'requestpath': '/mq/polysaas.odoo.invoice',
                'requestmethod': 'POST',
                'direction': 'REQ',
                'eventKey': 'polysaas.odoo.invoice.mattermost',
                'executescript': 'OdooInvoiceNotifierService',
                'description': 'Receive Odoo invoice MQ message → post Mattermost notification',
                'save_callbackdata': True,
            },
        ]

        for spec in INSTRUCTIONS:
            label = spec.pop('label')
            if dry_run:
                self.stdout.write(f'[DRY RUN] Would create/update: {label}')
                self.stdout.write(f'          requestpath={spec["requestpath"]}')
                self.stdout.write(f'          executescript={spec["executescript"]}')
                continue

            obj, created = Instruction.objects.update_or_create(
                tenant=tenant,
                requestpath=spec['requestpath'],
                requestmethod=spec['requestmethod'],
                defaults={k: v for k, v in spec.items()
                          if k not in ('requestpath', 'requestmethod')},
            )
            status = 'CREATED' if created else 'UPDATED'
            self.stdout.write(self.style.SUCCESS(
                f'[{status}] {label} (id={obj.pk})'
            ))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                '\nDone. The orchestration flow is now active:\n'
                '  Odoo invoice save → PolySniffer → EndpointDataExtractorService\n'
                '  → MQ topic polysaas.odoo.invoice.created\n'
                '  → OdooInvoiceNotifierService → Mattermost post\n'
            ))
