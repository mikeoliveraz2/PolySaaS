"""
Management command to set tenant themes for testing
"""
from django.core.management.base import BaseCommand
from dose.models import Tenant

class Command(BaseCommand):
    help = 'Set admin theme for a tenant'

    def add_arguments(self, parser):
        parser.add_argument('tenant_name', type=str, help='Name of the tenant')
        parser.add_argument('theme', type=str, help='Theme name (medical_blue, forest_green, royal_purple, sunset_orange, steel_gray)')

    def handle(self, *args, **options):
        tenant_name = options['tenant_name']
        theme = options['theme']
        
        # Validate theme choice
        valid_themes = [choice[0] for choice in Tenant.THEME_CHOICES]
        if theme not in valid_themes:
            self.stdout.write(
                self.style.ERROR(f'Invalid theme. Choose from: {", ".join(valid_themes)}')
            )
            return
        
        try:
            tenant = Tenant.objects.get(name__icontains=tenant_name)
            old_theme = tenant.get_admin_theme_display()
            tenant.admin_theme = theme
            tenant.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {tenant.name} theme from "{old_theme}" to "{tenant.get_admin_theme_display()}"'
                )
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Users assigned to "{tenant.name}" will now see the {tenant.get_admin_theme_display()} interface.'
                )
            )
            
        except Tenant.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Tenant with name containing "{tenant_name}" not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error updating tenant theme: {e}')
            )
