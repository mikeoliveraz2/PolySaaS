"""
Management command: setup_odoo_invoice_orchestration

Creates the default Instructions in the PUBLIC schema (tenant=None).

Design intent:
  - Instructions in public are global defaults inherited by all tenants.
  - New tenants automatically get these without any setup.
  - Future: tenants can override or disable public defaults via tenant-scoped
    Instructions that shadow the public ones.

Instructions created:

  1. DETECTOR — matches Odoo invoice create POST in the passthrough:
       requestpath: /web/dataset/call_kw/account.move/create
       executescript: EndpointDataExtractor
       → publishes to GCP Pub/Sub topic 'odoo-invoices'

Usage:
    python manage.py setup_odoo_invoice_orchestration
    python manage.py setup_odoo_invoice_orchestration --dry-run
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Create default Odoo invoice orchestration Instructions in public schema'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be created, no writes')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Force public schema — these are global defaults, not tenant-scoped
        with connection.cursor() as cur:
            cur.execute('SET search_path TO public;')

        self.stdout.write('Writing Instructions to: public schema (tenant=None — global defaults)')

        from dose.models import Instruction

        INSTRUCTIONS = [
            {
                'label': 'DETECTOR — Odoo invoice create passthrough hook',
                'requestpath': '/web/dataset/call_kw/account.move/create',
                'requestmethod': 'POST',
                'direction': 'REQ',
                'eventKey': 'polysaas.odoo.invoice.created',
                'executescript': 'EndpointDataExtractor',
                'description': 'Detect Odoo invoice create via passthrough -> extract & publish to GCP Pub/Sub odoo-invoices',
                'save_callbackdata': True,
            },
        ]

        for spec in INSTRUCTIONS:
            label = spec.pop('label')
            if dry_run:
                self.stdout.write(f'[DRY RUN] Would create/update: {label}')
                self.stdout.write(f'          requestpath={spec["requestpath"]}')
                self.stdout.write(f'          executescript={spec["executescript"]}')
                self.stdout.write(f'          tenant=None (public default)')
                continue

            obj, created = Instruction.objects.update_or_create(
                tenant=None,
                requestpath=spec['requestpath'],
                requestmethod=spec['requestmethod'],
                defaults={k: v for k, v in spec.items()
                          if k not in ('requestpath', 'requestmethod')},
            )
            status = 'CREATED' if created else 'UPDATED'
            self.stdout.write(self.style.SUCCESS(
                f'[{status}] {label} (id={obj.pk}, tenant=None/public)'
            ))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                '\nDone. Global default Instructions are now active in public schema.\n'
                '  Flow: Odoo invoice save -> PolySniffer -> EndpointDataExtractor\n'
                '        -> GCP Pub/Sub topic: odoo-invoices\n'
                '\n'
                '  All tenants inherit this by default.\n'
                '  Tenants can override by creating a tenant-scoped Instruction\n'
                '  with the same requestpath.\n'
            ))
