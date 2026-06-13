"""
Backfill dual Mattermost team membership for existing tenants.

Ensures each tenant MM user is on:
  - private company team (mm_team_id / mm_team_name)
  - shared collaboration team (mm_shared_team_id / mm_shared_team_name)

Usage:
    python manage.py ensure_dual_mattermost_teams --tenant-schema=polysast152
    python manage.py ensure_dual_mattermost_teams --all
"""

from django.core.management.base import BaseCommand

from dose.services.mattermost_tenant_provisioner import ensure_dual_mattermost_teams


class Command(BaseCommand):
    help = 'Backfill private + shared Mattermost team membership for tenant(s)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-schema',
            type=str,
            help='Single tenant schema (e.g. polysast152)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Process all tenants with a Mattermost TenantApp',
        )
        parser.add_argument(
            '--company-name',
            type=str,
            default='',
            help='Company display name when creating a missing private team',
        )

    def handle(self, *args, **options):
        if not options.get('tenant_schema') and not options.get('all'):
            self.stderr.write(self.style.ERROR('Pass --tenant-schema=<schema> or --all'))
            return

        schemas = []
        if options.get('all'):
            from dose.models import TenantApp

            for ta in TenantApp.objects.filter(app_name__icontains='mattermost').select_related('tenant'):
                schema = ta.tenant.schema_name
                if schema not in schemas:
                    schemas.append(schema)
        else:
            schemas = [options['tenant_schema']]

        ok, fail = 0, 0
        for schema in schemas:
            result = ensure_dual_mattermost_teams(
                schema,
                company_name=options.get('company_name') or '',
            )
            if result.get('success'):
                ok += 1
                self.stdout.write(self.style.SUCCESS(f'OK {schema}: {result.get("message")}'))
            else:
                fail += 1
                self.stderr.write(self.style.ERROR(f'FAIL {schema}: {result.get("error")}'))

        self.stdout.write(f'Done: {ok} ok, {fail} failed')
