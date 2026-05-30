from django.core.management.base import BaseCommand
from dose.models import TenantApp, Tenant

class Command(BaseCommand):
    help = 'Create Odoo TenantApp for a tenant (manual fix for missing provisioning)'

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str, help='Tenant slug (e.g., polysaast104)')
        parser.add_argument('--email', type=str, default='', help='Odoo login email')
        parser.add_argument('--password', type=str, default='PolySaaS2026!', help='Odoo password')

    def handle(self, *args, **options):
        slug = options['slug']
        email = options['email']
        password = options['password']
        
        try:
            t = Tenant.objects.get(slug=slug)
            self.stdout.write(f"Tenant: {t.name} (slug={t.slug}, schema={t.schema_name})")
            
            ta = TenantApp.objects.filter(tenant=t, app_name='odoo').first()
            if ta:
                self.stdout.write(self.style.WARNING(f"Odoo TenantApp already exists: {ta.status}"))
                return
            
            self.stdout.write("Creating Odoo TenantApp...")
            ta = TenantApp.objects.create(
                tenant=t,
                app_name='odoo',
                status='active',
                extra_config={
                    'odoo_login': email or f'{t.slug}@you.com',
                    'odoo_password': password,
                    'odoo_db': 'odoodb',
                    'odoo_url': 'https://polysaas-odoo2.onrender.com',
                }
            )
            self.stdout.write(self.style.SUCCESS(f"Created Odoo TenantApp: {ta.id}, status={ta.status}"))
            self.stdout.write(f"Extra config keys: {list(ta.extra_config.keys())}")
        except Tenant.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Tenant '{slug}' not found"))
