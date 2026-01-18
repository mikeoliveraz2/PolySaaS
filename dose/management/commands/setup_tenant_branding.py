"""
Management command to set up tenant branding and demo data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from dose.models import Tenant, Domain

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up tenant branding demo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-name',
            type=str,
            default='Demo Company',
            help='Name of the demo tenant'
        )
        parser.add_argument(
            '--domain',
            type=str,
            default='demo.localhost',
            help='Domain for the demo tenant'
        )

    def handle(self, *args, **options):
        tenant_name = options['tenant_name']
        domain_name = options['domain']

        # Create tenant
        tenant, created = Tenant.objects.get_or_create(
            schema_name='demo',
            defaults={
                'name': tenant_name,
                'tagline': 'Your Partner in Digital Excellence',
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created tenant: {tenant.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Tenant already exists: {tenant.name}')
            )

        # Create domain
        domain, created = Domain.objects.get_or_create(
            domain=domain_name,
            defaults={
                'tenant': tenant,
                'is_primary': True
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created domain: {domain.domain}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Domain already exists: {domain.domain}')
            )

        # Create tenant admin user
        if not User.objects.filter(username='admin', tenant=tenant).exists():
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@demo.com',
                password='admin123',
                tenant=tenant,
                is_staff=True,
                is_tenant_admin=True,
                is_superuser=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created admin user: {admin_user.username}')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Admin user already exists')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nTenant setup complete!\n'
                f'Tenant: {tenant.name}\n'
                f'Domain: {domain.domain}\n'
                f'Admin user: admin / admin123\n'
                f'You can now add a logo and customize the branding in the admin interface.'
            )
        )
