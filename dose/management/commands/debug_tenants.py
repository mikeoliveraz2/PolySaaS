from django.core.management.base import BaseCommand
from dose.models import Tenant

class Command(BaseCommand):
    help = 'List all tenants for debugging'

    def handle(self, *args, **options):
        self.stdout.write("=== Tenant Debugging ===")
        
        # Try normal queryset
        tenants = Tenant.objects.all()
        self.stdout.write(f"Normal queryset count: {tenants.count()}")
        
        for tenant in tenants:
            self.stdout.write(f"  - {tenant.name} ({tenant.schema_name})")
        
        # Try raw SQL
        try:
            raw_tenants = Tenant.objects.raw("SELECT * FROM public.dose_tenant")
            tenant_list = list(raw_tenants)
            self.stdout.write(f"\nRaw SQL count: {len(tenant_list)}")
            
            for tenant in tenant_list:
                self.stdout.write(f"  - {tenant.name} ({tenant.schema_name})")
        except Exception as e:
            self.stdout.write(f"Raw SQL failed: {e}")
        
        self.stdout.write("\n=== End Debug ===")
