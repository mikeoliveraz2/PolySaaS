from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dose.models import Tenant, UserProfile

class Command(BaseCommand):
    help = 'Assign users to tenants who do not have UserProfiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=int,
            help='Specific tenant ID to assign users to (optional)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        # Get users without UserProfiles
        users_without_profile = User.objects.filter(userprofile__isnull=True)
        
        if not users_without_profile.exists():
            self.stdout.write(
                self.style.SUCCESS('All users already have tenant assignments!')
            )
            return

        # Determine target tenant
        if options['tenant_id']:
            try:
                target_tenant = Tenant.objects.get(id=options['tenant_id'])
            except Tenant.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Tenant with ID {options["tenant_id"]} does not exist')
                )
                return
        else:
            # Get the first active tenant or create a default one
            target_tenant = Tenant.objects.filter(is_active=True).first()
            if not target_tenant:
                target_tenant = Tenant.objects.create(
                    name="Default Tenant",
                    slug="default",
                    description="Default tenant for existing users",
                    is_active=True
                )
                self.stdout.write(
                    self.style.WARNING('Created default tenant for existing users')
                )

        self.stdout.write(f'Found {users_without_profile.count()} users without tenant assignment')
        self.stdout.write(f'Target tenant: {target_tenant.name} (ID: {target_tenant.id})')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))
            for user in users_without_profile:
                self.stdout.write(f'Would assign: {user.username} ({user.email}) -> {target_tenant.name}')
        else:
            # Create UserProfiles for users without them
            created_count = 0
            for user in users_without_profile:
                UserProfile.objects.create(user=user, tenant=target_tenant)
                self.stdout.write(
                    f'✅ Assigned {user.username} ({user.email}) to {target_tenant.name}'
                )
                created_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} user-tenant assignments!')
            )
