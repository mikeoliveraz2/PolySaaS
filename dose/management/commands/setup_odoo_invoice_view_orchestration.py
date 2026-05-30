"""
Management command: setup_odoo_invoice_view_orchestration

Creates an Instruction to detect when users VIEW invoices in Odoo,
record the timestamp + invoice count to callback data, and write to dose_messages.

This instruction captures:
  - Timestamp of invoice view action
  - Number of invoices viewed (from response)
  - User information
  - Tenant context

Flow:
  1. User opens Odoo Invoices list (passthrough)
  2. PolySniffer detects the web_search_read call
  3. This instruction fires -> OdooInvoiceViewService
  4. Service extracts invoice count from response
  5. Writes to CallBackData with timestamp and count
  6. Creates DoseMessage for audit trail

Usage:
    python manage.py setup_odoo_invoice_view_orchestration
    python manage.py setup_odoo_invoice_view_orchestration --dry-run
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Create Odoo invoice VIEW orchestration Instruction in public schema'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be created, no writes')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Force public schema — these are global defaults, not tenant-scoped
        with connection.cursor() as cur:
            cur.execute('SET search_path TO public;')

        self.stdout.write('Writing Invoice VIEW Instruction to: public schema (tenant=None — global defaults)')

        from dose.models import Instruction

        INSTRUCTIONS = [
            {
                'label': 'DETECTOR — Odoo invoice VIEW (web_search_read) passthrough hook',
                'requestpath': '/web/dataset/call_kw/account.move/web_search_read',
                'requestmethod': 'POST',
                'direction': 'RES',  # Trigger on RESPONSE to capture invoice count
                'eventKey': 'polysaas.odoo.invoice.viewed',
                'executescript': 'OdooInvoiceViewService',
                'description': 'Detect Odoo invoice list view via passthrough -> record timestamp + invoice count to callback data and dose_messages',
                'save_callbackdata': True,
            },
            {
                'label': 'DETECTOR — Odoo invoice READ (read method) passthrough hook',
                'requestpath': '/web/dataset/call_kw/account.move/read',
                'requestmethod': 'POST',
                'direction': 'RES',  # Trigger on RESPONSE
                'eventKey': 'polysaas.odoo.invoice.read',
                'executescript': 'OdooInvoiceViewService',
                'description': 'Detect Odoo single invoice read via passthrough -> record timestamp + invoice details to callback data and dose_messages',
                'save_callbackdata': True,
            },
        ]

        for spec in INSTRUCTIONS:
            label = spec.pop('label')
            if dry_run:
                self.stdout.write(f'[DRY RUN] Would create/update: {label}')
                self.stdout.write(f'          requestpath={spec["requestpath"]}')
                self.stdout.write(f'          executescript={spec["executescript"]}')
                self.stdout.write(f'          direction={spec["direction"]}')
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
                '\nDone. Invoice VIEW Instructions are now active in public schema.\n'
                '  Flow: User views Odoo invoices -> PolySniffer detects web_search_read/read\n'
                '        -> OdooInvoiceViewService extracts count\n'
                '        -> Writes to CallBackData (timestamp, invoice_count)\n'
                '        -> Creates DoseMessage for audit\n'
                '\n'
                '  All tenants inherit this by default.\n'
            ))
