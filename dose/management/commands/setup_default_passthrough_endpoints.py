from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Setup default PassThroughEndpoint records for bundled apps (Odoo, Mattermost, etc.)"

    def add_arguments(self, parser):
        parser.add_argument('--odoo-url', default='http://localhost:8069', help="Odoo service URL")
        parser.add_argument('--mattermost-url', default='http://localhost:8065', help="Mattermost service URL")

    def handle(self, *args, **options):
        from dose.models import PassThroughEndpoint, Tenant

        self.stdout.write("\n" + "="*60)
        self.stdout.write("Setting up Default Passthrough Endpoints")
        self.stdout.write("="*60 + "\n")

        odoo_url = options['odoo_url']
        mattermost_url = options['mattermost_url']

        # Get first tenant
        tenant = Tenant.objects.first()
        if not tenant:
            self.stdout.write(self.style.ERROR("No tenant found. Please create a tenant first."))
            return

        self.stdout.write(f"Using tenant: {tenant.name} (schema: {tenant.schema_name})\n")

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

        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("Default Passthrough Endpoints Setup Complete!"))
        self.stdout.write("="*60)
        self.stdout.write(f"\nEndpoints configured:")
        self.stdout.write(f"  Odoo:      /pt/admin/odoo/ -> {odoo_ep.endpoint_url}")
        self.stdout.write(f"  Mattermost: /pt/admin/mattermost/ -> {mattermost_ep.endpoint_url}")
        self.stdout.write("\nThese will appear in the sidebar for tenants with active TenantApp records.")
        self.stdout.write("\nTenantApp records are created automatically during subscription when users select these apps.")
        self.stdout.write("\nNext steps:")
        self.stdout.write("1. Ensure Odoo and Mattermost services are running at the configured URLs")
        self.stdout.write("2. Test subscription flow to verify provisioning")
