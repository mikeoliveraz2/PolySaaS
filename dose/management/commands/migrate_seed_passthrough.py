from django.core.management.base import BaseCommand
from django.db import connection
from dose.models import Tenant, PassThroughEndpoint

class Command(BaseCommand):
    help = 'Migrate PassThroughEndpoint and seed endpoint for all tenants'

    def handle(self, *args, **options):
        for tenant in Tenant.objects.all():
            schema_name = tenant.schema_name
            self.stdout.write(f"Switching to schema: {schema_name}")
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO {schema_name},public;')
                # Check if PassThroughEndpoint exists
                from django.apps import apps
                PassThroughEndpoint = apps.get_model('dose', 'PassThroughEndpoint')
                endpoint_url = input(f"Enter passthrough endpoint URL for tenant '{tenant.name}' ({schema_name}): ")
                if not PassThroughEndpoint.objects.exists():
                    PassThroughEndpoint.objects.create(tenant=tenant, endpoint_url=endpoint_url, description=f"Endpoint for {tenant.name}")
                    self.stdout.write(self.style.SUCCESS(f"Created PassThroughEndpoint for tenant {tenant.name} ({schema_name})"))
                else:
                    self.stdout.write(self.style.WARNING(f"PassThroughEndpoint already exists for tenant {tenant.name} ({schema_name})"))
            # Reset search_path to public
            with connection.cursor() as cursor:
                cursor.execute('SET search_path TO public;')
        self.stdout.write(self.style.SUCCESS('Migration and seeding complete.'))
