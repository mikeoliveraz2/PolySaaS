from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Setup default PassThroughEndpoint records for bundled apps (Odoo, Mattermost, etc.)"

    def add_arguments(self, parser):
        parser.add_argument('--odoo-url', default='http://localhost:8069', help="Odoo service URL")
        parser.add_argument('--mattermost-url', default='http://localhost:8065', help="Mattermost service URL")
        parser.add_argument('--nextcloud-url', default='http://localhost:8080', help="NextCloud service URL")
        parser.add_argument('--tenant-slug', help="Specific tenant slug to setup endpoints for (default: first tenant)")

    def handle(self, *args, **options):
        from dose.models import PassThroughEndpoint, Tenant
        from django.db import connection

        self.stdout.write("\n" + "="*60)
        self.stdout.write("Setting up Default Passthrough Endpoints")
        self.stdout.write("="*60 + "\n")

        odoo_url = options['odoo_url']
        mattermost_url = options['mattermost_url']

        # Get tenant - either by slug or first available
        tenant_slug = options.get('tenant_slug')
        if tenant_slug:
            try:
                tenant = Tenant.objects.get(slug=tenant_slug)
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Tenant with slug '{tenant_slug}' not found."))
                return
        else:
            tenant = Tenant.objects.first()
            if not tenant:
                self.stdout.write(self.style.ERROR("No tenant found. Please create a tenant first."))
                return

        self.stdout.write(f"Using tenant: {tenant.name} (schema: {tenant.schema_name})\n")

        # CRITICAL: Set search_path to tenant schema so endpoints are created there
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO "{tenant.schema_name}"')
            self.stdout.write(f"Set search_path to tenant schema: {tenant.schema_name}\n")

        # 1. Odoo PassThroughEndpoint
        odoo_ep, created = PassThroughEndpoint.objects.update_or_create(
            trigger_path='odoo',
            defaults={
                'endpoint_url': odoo_url,
                'description': 'Odoo ERP - tenant-specific instance',
                'is_enabled': True,
                'passthrough_type': 'scraper',
                'integration_mode': 'web_api',
                'api_endpoint': f"{odoo_url}/xmlrpc/2",
                'show_in_menu': True,
                'menu_title': 'Odoo',
                'menu_icon': 'building',
                'menu_sort_order': 20,
                'auth_username': 'admin',
                'auth_password': 'admin',
                'starting_uri': '/web',
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Created Odoo PassThroughEndpoint: {odoo_url}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✓ Odoo PassThroughEndpoint already exists: {odoo_ep.endpoint_url}"))
            if odoo_ep.endpoint_url != odoo_url:
                odoo_ep.endpoint_url = odoo_url
                odoo_ep.save()
                self.stdout.write(self.style.SUCCESS(f"  Updated URL to: {odoo_url}"))

        # 2. Mattermost PassThroughEndpoint
        mattermost_ep, created = PassThroughEndpoint.objects.update_or_create(
            trigger_path='mattermost',
            defaults={
                'endpoint_url': mattermost_url,
                'description': 'Mattermost Team Chat - tenant-specific team',
                'is_enabled': True,
                'passthrough_type': 'scraper',
                'integration_mode': 'web_api',
                'api_endpoint': f"{mattermost_url}/api/v4",
                'show_in_menu': True,
                'menu_title': 'Mattermost',
                'menu_icon': 'chat',
                'menu_sort_order': 25,
                'starting_uri': '/',
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Created Mattermost PassThroughEndpoint: {mattermost_url}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✓ Mattermost PassThroughEndpoint already exists: {mattermost_ep.endpoint_url}"))
            if mattermost_ep.endpoint_url != mattermost_url:
                mattermost_ep.endpoint_url = mattermost_url
                mattermost_ep.save()
                self.stdout.write(self.style.SUCCESS(f"  Updated URL to: {mattermost_url}"))

        # 3. NextCloud PassThroughEndpoint
        nextcloud_url = options['nextcloud_url']
        nextcloud_ep, created = PassThroughEndpoint.objects.update_or_create(
            trigger_path='nextcloud',
            defaults={
                'endpoint_url': nextcloud_url,
                'description': 'NextCloud File Storage - tenant-specific instance',
                'is_enabled': True,
                'passthrough_type': 'scraper',
                'integration_mode': 'web_api',
                'api_endpoint': f"{nextcloud_url}/ocs/v1.php",
                'show_in_menu': True,
                'menu_title': 'NextCloud',
                'menu_icon': 'cloud',
                'menu_sort_order': 30,
                'starting_uri': '/',
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Created NextCloud PassThroughEndpoint: {nextcloud_url}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✓ NextCloud PassThroughEndpoint already exists: {nextcloud_ep.endpoint_url}"))
            if nextcloud_ep.endpoint_url != nextcloud_url:
                nextcloud_ep.endpoint_url = nextcloud_url
                nextcloud_ep.save()
                self.stdout.write(self.style.SUCCESS(f"  Updated URL to: {nextcloud_url}"))

        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("Default Passthrough Endpoints Setup Complete!"))
        self.stdout.write("="*60)
        self.stdout.write(f"\nEndpoints configured:")
        self.stdout.write(f"  Odoo:      /pt/admin/odoo/ -> {odoo_ep.endpoint_url}")
        self.stdout.write(f"  Mattermost: /pt/admin/mattermost/ -> {mattermost_ep.endpoint_url}")
        self.stdout.write(f"  NextCloud:  /pt/admin/nextcloud/ -> {nextcloud_ep.endpoint_url}")
        self.stdout.write("\nThese will appear in the sidebar for tenants with active TenantApp records.")
        self.stdout.write("\nTenantApp records are created automatically during subscription when users select these apps.")
        self.stdout.write("\nNext steps:")
        self.stdout.write("1. Ensure Odoo, Mattermost, and NextCloud services are running at the configured URLs")
        self.stdout.write("2. Test subscription flow to verify provisioning")
