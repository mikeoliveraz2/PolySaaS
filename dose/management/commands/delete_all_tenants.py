from django.core.management.base import BaseCommand
from dose.models import Tenant, UserProfile
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Delete all tenants and related user profiles.'

    def handle(self, *args, **options):
        self.stdout.write('Deleting all user profiles...')
        UserProfile.objects.all().delete()
        self.stdout.write('Deleting all tenants...')
        Tenant.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('All tenants and user profiles deleted.'))
