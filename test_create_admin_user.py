# Test script to create a user and tenant with admin permissions
from django.contrib.auth import get_user_model
from dose.models import Tenant, UserProfile, UserTenantMembership
import uuid

unique = uuid.uuid4().hex[:8]
username = f"testadmin_{unique}"
email = f"{username}@polysaas.online"
password = "PolySaaS2026!"
tenant_name = f"Test Tenant {unique}"
tenant_slug = f"testtenant_{unique}"
schema_name = tenant_slug

User = get_user_model()

# Create tenant
tenant, created = Tenant.objects.get_or_create(
    name=tenant_name,
    defaults={
        'slug': tenant_slug,
        'schema_name': schema_name,
        'description': 'Created via test script.'
    }
)

# Create user
user = User.objects.create_user(username=username, email=email, password=password)
user.is_staff = True
user.is_superuser = True
user.save()

# Fetch user profile (should be auto-created by signal)
profile = UserProfile.objects.get(user=user)
UserTenantMembership.objects.get_or_create(
    user=user, tenant=tenant,
    defaults={'role': UserTenantMembership.Role.OWNER},
)

print(f"Created user: {username} / {email} / {password}")
print(f"Created tenant: {tenant_name} (slug: {tenant_slug})")
print(f"User is_staff: {user.is_staff}, is_superuser: {user.is_superuser}")
print(f"User profile tenant: {profile.tenant}")
