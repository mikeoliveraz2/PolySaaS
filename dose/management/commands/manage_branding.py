"""
Management command to help manage tenant branding
"""
from django.core.management.base import BaseCommand
from django.core.files import File
from dose.models import Tenant
import os


class Command(BaseCommand):
    help = 'Manage tenant branding (logos and taglines)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all tenants and their branding status'
        )
        parser.add_argument(
            '--tenant-id',
            type=int,
            help='Tenant ID to update'
        )
        parser.add_argument(
            '--set-tagline',
            type=str,
            help='Set tagline for specified tenant'
        )
        parser.add_argument(
            '--logo-path',
            type=str,
            help='Path to logo file to upload'
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_tenants()
        elif options['tenant_id']:
            self.update_tenant(options)
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --list or --tenant-id')
            )

    def list_tenants(self):
        """List all tenants and their branding status"""
        self.stdout.write(
            self.style.SUCCESS('\n=== Tenant Branding Status ===\n')
        )
        
        tenants = Tenant.objects.all()
        if not tenants:
            self.stdout.write(
                self.style.WARNING('No tenants found.')
            )
            return
            
        for tenant in tenants:
            logo_status = "✓ Has logo" if tenant.logo else "✗ No logo"
            tagline_status = f"✓ \"{tenant.tagline}\"" if tenant.tagline and tenant.tagline != 'N/A' else "✗ No tagline"
            
            self.stdout.write(f"ID: {tenant.id} | Name: {tenant.name}")
            self.stdout.write(f"  Schema: {tenant.schema_name}")
            self.stdout.write(f"  Logo: {logo_status}")
            self.stdout.write(f"  Tagline: {tagline_status}")
            self.stdout.write("")

    def update_tenant(self, options):
        """Update tenant branding"""
        tenant_id = options['tenant_id']
        
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Tenant with ID {tenant_id} not found.')
            )
            return
            
        # Update tagline
        if options['set_tagline']:
            tenant.tagline = options['set_tagline']
            tenant.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated tagline for {tenant.name}: "{options["set_tagline"]}"')
            )
            
        # Update logo
        if options['logo_path']:
            logo_path = options['logo_path']
            if not os.path.exists(logo_path):
                self.stdout.write(
                    self.style.ERROR(f'Logo file not found: {logo_path}')
                )
                return
                
            with open(logo_path, 'rb') as logo_file:
                tenant.logo.save(
                    os.path.basename(logo_path),
                    File(logo_file),
                    save=True
                )
            self.stdout.write(
                self.style.SUCCESS(f'Updated logo for {tenant.name}: {logo_path}')
            )
            
        self.stdout.write(
            self.style.SUCCESS(f'\nTenant "{tenant.name}" branding updated successfully!')
        )
