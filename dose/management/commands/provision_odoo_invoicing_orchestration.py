# THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
# BINGO: Demo Tenant Odoo invoicing orchestration backfill — 2026-06-12

"""
Backfill Odoo Invoicing orchestration Instructions for existing tenants.

Usage:
    python manage.py provision_odoo_invoicing_orchestration polysaast151
    python manage.py provision_odoo_invoicing_orchestration --all-odoo-active
"""
from django.core.management.base import BaseCommand

from dose.models import Tenant, TenantApp
from dose.services.odoo_orchestration_provisioner import provision_odoo_invoicing_orchestration


class Command(BaseCommand):
    help = 'Provision Odoo Invoicing orchestration Instructions for one or more tenants'

    def add_arguments(self, parser):
        parser.add_argument(
            'slug', nargs='?', type=str, default='',
            help='Tenant slug (e.g. polysaast151)',
        )
        parser.add_argument(
            '--all-odoo-active', action='store_true',
            help='Provision for every tenant with an active Odoo TenantApp',
        )
        parser.add_argument(
            '--menu-id', type=int, default=None,
            help='Override invoicing menu_id (default: discover from Odoo)',
        )

    def handle(self, *args, **options):
        slug = (options.get('slug') or '').strip()
        all_active = options.get('all_odoo_active')
        menu_id = options.get('menu_id')

        tenants = []
        if all_active:
            seen = set()
            for ta in TenantApp.public_bundles.filter(
                app_name='odoo', status='active',
            ).select_related('tenant'):
                if ta.tenant and ta.tenant.pk not in seen:
                    seen.add(ta.tenant.pk)
                    tenants.append(ta.tenant)
            self.stdout.write(f'Found {len(tenants)} tenant(s) with active Odoo')
        elif slug:
            try:
                tenants = [Tenant.objects.get(slug=slug)]
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Tenant '{slug}' not found"))
                return
        else:
            self.stdout.write(self.style.ERROR(
                'Provide a tenant slug (e.g. polysaast151) or use --all-odoo-active'
            ))
            return

        for tenant in tenants:
            self.stdout.write(
                f'Provisioning invoicing orchestration for {tenant.name} ({tenant.slug})...'
            )
            result = provision_odoo_invoicing_orchestration(tenant, menu_id=menu_id)
            if result.get('success'):
                self.stdout.write(self.style.SUCCESS(
                    f"  OK menu_id={result.get('menu_id')} "
                    f"instructions={result.get('instruction_ids')}"
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f"  Failed: {result.get('error', 'unknown')}"
                ))
