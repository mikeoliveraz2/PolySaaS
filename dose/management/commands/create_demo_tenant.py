from django.core.management.base import BaseCommand
from dose.models import Tenant, Domain

class Command(BaseCommand):
    help = 'Create a demo tenant for testing'

    def handle(self, *args, **options):
        try:
            # Check if demo tenant already exists
            demo_tenant = Tenant.objects.filter(schema_name='demo').first()
            if not demo_tenant:
                demo_tenant = Tenant.objects.create(
                    schema_name='demo',
                    name='Demo Tenant',
                    tagline='Demo Environment'
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created demo tenant: {demo_tenant}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Demo tenant already exists: {demo_tenant}')
                )
            
            # Create domain for the demo tenant  
            demo_domain = Domain.objects.filter(domain='localhost', tenant=demo_tenant).first()
            if not demo_domain:
                demo_domain = Domain.objects.create(
                    domain='localhost',
                    tenant=demo_tenant,
                    is_primary=True
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created demo domain: {demo_domain}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Demo domain already exists: {demo_domain}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating tenant: {e}')
            )
            import traceback
            traceback.print_exc()
