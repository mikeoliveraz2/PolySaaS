from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dose.models import Tenant, UserProfile
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create demo tenant and demo user, and link them via UserProfile.'

    def handle(self, *args, **options):
        tenant, t_created = Tenant.objects.get_or_create(
            slug='demo', defaults={
                'name': 'DemoTenant',
                'schema_name': 'demo',
                'created_at': timezone.now()
            })
        user, u_created = User.objects.get_or_create(
            username='demouser', defaults={'email': 'demo@example.com'})
        user.set_password('demopass')
        # Always ensure demo user is active and staff
        if not user.is_active or not user.is_staff:
            user.is_active = True
            user.is_staff = True
            user.save()
        profile, p_created = UserProfile.objects.get_or_create(user=user, tenant=tenant)
        self.stdout.write(self.style.SUCCESS('Demo tenant, user, and profile ensured.'))
