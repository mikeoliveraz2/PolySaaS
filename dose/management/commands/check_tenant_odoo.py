from django.core.management.base import BaseCommand
from dose.models import TenantApp, Tenant

class Command(BaseCommand):
    help = 'Check Odoo TenantApp status and credentials'

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str, help='Tenant slug (e.g., t104)')

    def handle(self, *args, **options):
        slug = options['slug']
        try:
            t = Tenant.objects.get(slug=slug)
            ta = TenantApp.objects.filter(tenant=t, app_name='odoo').first()
            
            self.stdout.write(f"Tenant: {t.name} (slug={t.slug}, schema={t.schema_name})")
            self.stdout.write(f"TenantApp status: {ta.status if ta else 'None'}")
            if ta:
                self.stdout.write(f"TenantApp last_error: {ta.last_error}")
                if ta.extra_config and isinstance(ta.extra_config, dict):
                    self.stdout.write(f"Extra config keys: {list(ta.extra_config.keys())}")
                    self.stdout.write(f"  odoo_login: {ta.extra_config.get('odoo_login')}")
                    self.stdout.write(f"  odoo_db: {ta.extra_config.get('odoo_db')}")
                    self.stdout.write(f"  odoo_url: {ta.extra_config.get('odoo_url')}")
                    self.stdout.write(f"  odoo_session_id: {ta.extra_config.get('odoo_session_id', 'None')}")
        except Tenant.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Tenant '{slug}' not found"))
