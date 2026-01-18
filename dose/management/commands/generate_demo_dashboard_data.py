from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from dose.models import Tenant, RequestLog, ErrorLog
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Generate demo data for dashboard charts (RequestLog, ErrorLog)'

    def handle(self, *args, **options):
        from dose.models import UserProfile
        tenant = Tenant.objects.first()
        if not tenant:
            tenant = Tenant.objects.create(name='DemoTenant', slug='demo', schema_name='demo', created_at=timezone.now())
            self.stdout.write(self.style.WARNING('Demo tenant created.'))
        tenant = Tenant.objects.filter(slug='demo').first()
        if not tenant:
            self.stdout.write(self.style.ERROR('Demo tenant not found. Run create_demo_user_and_tenant first.'))
            return
        # Create 25 demo users and assign to demo tenant
        demo_users = []
        for i in range(25):
            username = f'demouser{i+1}'
            email = f'demo{i+1}@example.com'
            user, created = User.objects.get_or_create(username=username, defaults={'email': email})
            user.set_password('demopass')
            user.is_active = True
            user.is_staff = True
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user, tenant=tenant)
            demo_users.append(user)
        now = timezone.now()
        # Create 50 request logs in the last hour, randomly assign to demo users
        for i in range(50):
            ts = now - timedelta(minutes=random.randint(0, 59))
            req_user = random.choice(demo_users)
            RequestLog.objects.create(
                tenant=tenant,
                user=req_user,
                path=f'/dose/api/test/{i}',
                method=random.choice(['GET', 'POST', 'PUT']),
                timestamp=ts
            )
        # Create 10 error logs in the last hour, randomly assign to demo users
        for i in range(10):
            ts = now - timedelta(minutes=random.randint(0, 59))
            err_user = random.choice(demo_users)
            ErrorLog.objects.create(
                tenant=tenant,
                user=err_user,
                error_message=f'Demo error {i} occurred',
                path=f'/dose/api/test/{i}',
                status_code=random.choice([400, 401, 403, 404, 500]),
                timestamp=ts
            )
        self.stdout.write(self.style.SUCCESS('Demo dashboard data generated with 25 active users.'))
