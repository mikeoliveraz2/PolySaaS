from django.core.management.base import BaseCommand
from dose.models import TenantApp


class Command(BaseCommand):
    help = 'Update Mattermost team names in TenantApp extra_config'

    def handle(self, *args, **options):
        updated_count = 0
        for ta in TenantApp.objects.filter(app_name='mattermost'):
            config = ta.extra_config or {}
            old_value = config.get('mm_team_name', 'NOT SET')
            
            config['mm_team_name'] = 'PolySaaS-Dev-Team'
            ta.extra_config = config
            ta.save(update_fields=['extra_config'])
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ {ta.tenant.name}: mm_team_name {old_value} → PolySaaS-Dev-Team'
                )
            )
            updated_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\nUpdated {updated_count} Mattermost TenantApps'))
