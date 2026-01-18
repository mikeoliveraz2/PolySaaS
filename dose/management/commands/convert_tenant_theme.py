from django.core.management.base import BaseCommand
from dose.models import Tenant
from admin_interface.models import Theme

class Command(BaseCommand):
    help = 'Convert old admin_theme string values to Theme ForeignKey references.'

    def handle(self, *args, **options):
        theme_map = {theme.name.lower().replace(' ', '_'): theme.id for theme in Theme.objects.all()}
        updated = 0
        for tenant in Tenant.objects.all():
            if isinstance(tenant.admin_theme, str):
                theme_key = tenant.admin_theme.lower().replace(' ', '_')
                theme_id = theme_map.get(theme_key)
                if theme_id:
                    tenant.admin_theme_id = theme_id
                    tenant.save(update_fields=['admin_theme'])
                    updated += 1
                else:
                    self.stdout.write(self.style.WARNING(f'No Theme found for "{tenant.admin_theme}"'))
        self.stdout.write(self.style.SUCCESS(f'Updated {updated} tenants.'))
