"""Re-run Odoo provisioning for an existing tenant (fix stuck/error TenantApps)."""
from django.core.management.base import BaseCommand

from dose.models import Tenant, TenantApp
from dose.services.odoo_tenant_provisioner import provision_odoo_tenant


class Command(BaseCommand):
    help = 'Re-provision Odoo user and PassThroughEndpoint for a tenant slug'

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str, help='Tenant slug (e.g. polysaast3)')
        parser.add_argument('--email', type=str, default='', help='Override Odoo login email')
        parser.add_argument('--password', type=str, default='', help='Override Odoo user password')

    def handle(self, *args, **options):
        slug = options['slug']
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Tenant '{slug}' not found"))
            return

        ta = TenantApp.objects.filter(tenant=tenant, app_name='odoo').first()
        if not ta:
            self.stdout.write(self.style.ERROR(f"No Odoo TenantApp for {slug}"))
            return

        extra = ta.extra_config if isinstance(ta.extra_config, dict) else {}
        admin_email = options['email'] or extra.get('odoo_login') or ''
        if not admin_email:
            self.stdout.write(self.style.ERROR('No odoo_login in TenantApp and --email not provided'))
            return

        admin_password = options['password'] or extra.get('odoo_password') or ''

        self.stdout.write(f"Re-provisioning Odoo for {tenant.name} ({slug}) login={admin_email}")
        result = provision_odoo_tenant(
            tenant_schema=tenant.schema_name,
            tenant_name=tenant.name,
            admin_email=admin_email,
            company_name=tenant.name,
            tenant_app_id=ta.id,
            admin_password=admin_password,
        )

        if result.get('success'):
            self.stdout.write(self.style.SUCCESS(
                f"OK — odoo_user_id={result.get('odoo_user_id')} status=active"
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"Failed — {result.get('error') or result.get('message')}"
            ))
