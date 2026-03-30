"""
Management command: create_sniffer_stream_actions

For every PassThroughEndpoint that has sniffed POST traffic (TrafficLog entries),
creates an Instruction + MQOutput for each unique POST path.

Usage:
    python manage.py create_sniffer_stream_actions
    python manage.py create_sniffer_stream_actions --tenant olient
    python manage.py create_sniffer_stream_actions --dry-run
    python manage.py create_sniffer_stream_actions --endpoint odoo
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Auto-create Instruction + MQOutput stream actions from PolySniffer POST traffic. '
        'Topic name format: {endpoint_trigger}-{post_path_slug}'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            default=None,
            help='Schema name of the tenant to create records under (default: public)',
        )
        parser.add_argument(
            '--endpoint',
            type=str,
            default=None,
            help='Only process endpoints whose trigger_path contains this string',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Show what would be created without writing to the database',
        )

    def handle(self, *args, **options):
        from dose.models.tenant import Tenant
        from dose.models.pass_through_endpoint import PassThroughEndpoint
        from dose.services.sniffer_stream_actions import (
            create_stream_actions_for_endpoint,
            create_stream_actions_for_all_sniffed,
        )

        dry_run = options['dry_run']
        tenant_schema = options['tenant']
        endpoint_filter = options['endpoint']

        # Resolve tenant
        tenant = None
        if tenant_schema:
            try:
                tenant = Tenant.objects.get(schema_name=tenant_schema)
                self.stdout.write(f'Using tenant: {tenant.name} ({tenant.schema_name})')
            except Tenant.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Tenant with schema "{tenant_schema}" not found.'))
                return
        else:
            self.stdout.write('No tenant specified — records will have tenant=None (public schema)')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no records will be written'))

        # Filter endpoints
        if endpoint_filter:
            endpoints = PassThroughEndpoint.objects.filter(
                trigger_path__icontains=endpoint_filter
            )
            if not endpoints.exists():
                self.stderr.write(self.style.ERROR(
                    f'No endpoints found with trigger_path containing "{endpoint_filter}"'
                ))
                return
        else:
            endpoints = None  # will use all-sniffed scan

        total_created = 0
        total_skipped = 0

        if endpoints is not None:
            for ep in endpoints:
                results = create_stream_actions_for_endpoint(ep, tenant, dry_run=dry_run)
                self._print_results(results)
                for r in results:
                    if r.get('status') == 'created':
                        total_created += 1
                    else:
                        total_skipped += 1
        else:
            results = create_stream_actions_for_all_sniffed(tenant, dry_run=dry_run)
            self._print_results(results)
            for r in results:
                if r.get('status') == 'created':
                    total_created += 1
                else:
                    total_skipped += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done. Created: {total_created}  |  Skipped/existing: {total_skipped}'
        ))

    def _print_results(self, results):
        for r in results:
            status = r.get('status', '?')
            endpoint = r.get('endpoint', '?')
            path = r.get('path', '')
            topic = r.get('topic', '')

            if status == 'created':
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  [CREATED] {endpoint}  path={path}  topic={topic}'
                        f'  instruction_id={r.get("instruction_id")}  mq_output_id={r.get("mq_output_id")}'
                    )
                )
            elif status == 'already_exists':
                self.stdout.write(f'  [EXISTS]  {endpoint}  path={path}  topic={topic}')
            elif status == 'dry_run':
                self.stdout.write(
                    self.style.WARNING(
                        f'  [DRY-RUN] {endpoint}  path={path}  would create topic={topic}'
                    )
                )
            elif status == 'no_posts_found':
                self.stdout.write(f'  [SKIP]    {endpoint}  — no POST traffic in PolySniffer')
            elif status == 'no_sniffed_endpoints_found':
                self.stdout.write(self.style.WARNING('  No sniffed endpoints found with POST traffic.'))
            else:
                self.stdout.write(f'  [{status}] {r}')
