"""Backfill PassThroughEndpoint catalog rows in a tenant schema."""
from django.core.management.base import BaseCommand

from dose.management.passthrough_seed import seed_passthrough_endpoints
from dose.models import Tenant


class Command(BaseCommand):
    help = 'Seed PassThroughEndpoint rows into a tenant schema (for sidebar passthrough links)'

    def add_arguments(self, parser):
        parser.add_argument('slug', nargs='?', default='', help='Tenant slug (e.g. polysaasppd)')
        parser.add_argument(
            '--all-empty', action='store_true',
            help='Seed every tenant schema that has zero PassThroughEndpoint rows',
        )

    def handle(self, *args, **options):
        slug = (options.get('slug') or '').strip()
        all_empty = options.get('all_empty')

        if all_empty:
            tenants = []
            for t in Tenant.objects.exclude(schema_name__in=['', 'public']).order_by('slug'):
                tenants.append(t)
            self.stdout.write(f'Checking {len(tenants)} tenant(s)...')
        elif slug:
            try:
                tenants = [Tenant.objects.get(slug=slug)]
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Tenant '{slug}' not found"))
                return
        else:
            self.stdout.write(self.style.ERROR('Provide a tenant slug or use --all-empty'))
            return

        for tenant in tenants:
            if all_empty:
                from django.db import connection
                from dose.models import PassThroughEndpoint
                with connection.cursor() as cur:
                    cur.execute(f'SET search_path TO "{tenant.schema_name}",public;')
                if PassThroughEndpoint.objects.exists():
                    continue
            n = seed_passthrough_endpoints(tenant, log=self.stdout.write)
            if n:
                self.stdout.write(self.style.SUCCESS(f'{tenant.slug}: seeded {n} endpoint(s)'))
            elif not all_empty:
                self.stdout.write(f'{tenant.slug}: nothing to seed (already present or no donor)')
